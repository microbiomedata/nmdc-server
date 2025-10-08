import datetime
import logging
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
import requests
from google.cloud import secretmanager
from sqlalchemy import text

from nmdc_server import jobs
from nmdc_server.config import settings
from nmdc_server.database import SessionLocal, SessionLocalIngest
from nmdc_server.ingest import errors
from nmdc_server.models import SubmissionImagesObject
from nmdc_server.static_files import generate_submission_schema_files, initialize_static_directory
from nmdc_server.storage import BucketName, storage


def swap_gcp_secret_values(gcp_project_id: str, secret_a_id: str, secret_b_id: str) -> None:
    """Swaps the values of two secrets in Google Secret Manager.

    Note: To update a secret's content, we "add a version" of that secret.

    TODO: Consider having both versions of the secret pre-created on GCP,
          and then—here—just activate one version or the other. That could
          make it so we aren't storing so many versions of each secret.

    References (note: the `noqa` comment prevents the linter from flagging the line length):
    - Importing the Python library: https://cloud.google.com/secret-manager/docs/reference/libraries#client-libraries-install-python  # noqa: E501
    - Add secret version: https://cloud.google.com/secret-manager/docs/samples/secretmanager-add-secret-version  # noqa: E501
    """

    client = secretmanager.SecretManagerServiceClient()

    # Get the initial value of the first secret.
    secret_a_path = client.secret_path(gcp_project_id, secret_a_id)
    request = secretmanager.AccessSecretVersionRequest(
        name=f"{secret_a_path}/versions/latest"
    )
    response = client.access_secret_version(request=request)
    secret_a_value: bytes = response.payload.data
    click.echo(f"Read secret: {secret_a_path}")

    # Get the initial value of the second secret.
    secret_b_path = client.secret_path(gcp_project_id, secret_b_id)
    request = secretmanager.AccessSecretVersionRequest(
        name=f"{secret_b_path}/versions/latest"
    )
    response = client.access_secret_version(request=request)
    secret_b_value: bytes = response.payload.data
    click.echo(f"Read secret: {secret_b_path}")

    # Put the second secret's initial value into the first secret.
    payload = secretmanager.SecretPayload(data=secret_b_value)
    request = secretmanager.AddSecretVersionRequest(
        parent=secret_a_path, payload=payload
    )
    _ = client.add_secret_version(request=request)
    click.echo(f"Updated secret: {secret_a_path}")

    # Put the first secret's initial value into the second secret.
    payload = secretmanager.SecretPayload(data=secret_a_value)
    request = secretmanager.AddSecretVersionRequest(
        parent=secret_b_path, payload=payload
    )
    _ = client.add_secret_version(request=request)
    click.echo(f"Updated secret: {secret_b_path}")


def send_slack_message(text: str) -> bool:
    r"""
    Sends a Slack message having the specified text if the application has
    a Slack Incoming Webhook URL defined. If the application does not have
    a Slack Incoming Webhook URL defined, no message is sent.

    The function returns `True` if the message was sent; otherwise, `False`.

    Reference: https://api.slack.com/messaging/webhooks#posting_with_webhooks
    """
    is_sent = False

    # Check whether a Slack Incoming Webhook URL is defined.
    if isinstance(settings.slack_webhook_url_for_ingester, str):
        click.echo(f"Sending Slack message having text: {text}")
        response = requests.post(
            settings.slack_webhook_url_for_ingester,
            json={"text": text},
            headers={"Content-type": "application/json"},
        )

        # Check whether the message was sent successfully.
        if response.status_code == 200:
            click.echo("Sent Slack message.")
            is_sent = True
        else:
            click.echo("Failed to send Slack message.", err=True)
    else:
        click.echo("No Slack Incoming Webhook URL is defined.", err=True)

    return is_sent


@click.group()
@click.pass_context
def cli(ctx):
    if settings.environment == "testing":
        settings.database_uri = settings.testing_database_uri
    ctx.obj = {"settings": settings}


@cli.command()
def create_or_replace_nmdc_functions():
    """Create or replace custom NMDC functions for the SQL Databases"""
    jobs.update_nmdc_functions()


@cli.command()
@click.option("--ingest-db", is_flag=True, default=False)
def migrate(ingest_db: bool):
    """Upgrade the database schema."""
    jobs.migrate(ingest_db=ingest_db)


@cli.command()
def truncate():
    """Remove all existing data from the ingest database."""
    with SessionLocalIngest() as db:
        try:
            db.execute(text("select truncate_tables()")).all()
            db.commit()
        except Exception:
            db.rollback()
            db.execute(
                text(
                    """
                DO $$ DECLARE
                     r RECORD;
                 BEGIN
                     FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = current_schema())
                     LOOP
                         EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                     END LOOP;
                 END $$;
            """
                )
            )
            db.commit()


@cli.command()
@click.option("-v", "--verbose", count=True)
@click.option("--function-limit", type=click.INT, default=100)
@click.option("--skip-annotation", is_flag=True, default=False)
@click.option(
    "--swap-rancher-secrets",
    is_flag=True,
    default=False,
    help="Swap secrets on Spin via the Rancher API",
)
@click.option(
    "--swap-google-secrets",
    is_flag=True,
    default=False,
    help="Swap secrets on Google Secret Manager via its API",
)
def ingest(
    verbose, function_limit, skip_annotation, swap_rancher_secrets, swap_google_secrets: bool
):
    """Ingest the latest data from mongo into the ingest database."""
    level = logging.WARN
    if verbose == 1:
        level = logging.INFO
    elif verbose > 1:
        level = logging.DEBUG
    logging.basicConfig(level=level, format="%(message)s")

    # Get the current time as a human-readable string that indicates the timezone.
    ingest_start_datetime = datetime.datetime.now(datetime.timezone.utc)
    ingest_start_datetime_str = ingest_start_datetime.isoformat(timespec="seconds")

    # Send a Slack message announcing that this ingest is starting.
    send_slack_message(
        f"Ingest is starting.\n"
        f"• Start time: `{ingest_start_datetime_str}`\n"
        f"• MongoDB host: `{settings.mongo_host}`"
    )

    try:
        jobs.do_ingest(function_limit, skip_annotation)
    except Exception as e:
        send_slack_message(
            f"Ingest failed.\n"
            f"• Start time: `{ingest_start_datetime_str}`\n"
            f"• MongoDB host: `{settings.mongo_host}`\n"
            f"• Error message: {e}"
        )

        # Now that we've processed the Exception at this level, propagate it.
        raise e

    for m, s in errors.missing.items():
        click.echo(f"missing {m}:")
        for id in s:
            click.echo(id)

    for m, s in errors.errors.items():
        click.echo(f"errors {m}:")
        for id in s:
            click.echo(id)

    if swap_rancher_secrets:

        # TODO: Move this validation to the top of the ingest function so we fail early.
        def require_setting(name: str):
            if not getattr(settings, name, None):
                raise ValueError(f"{name} must be set to use --swap-rancher-secrets")

        require_setting("rancher_api_base_url")
        require_setting("rancher_api_auth_token")
        require_setting("rancher_project_id")
        require_setting("rancher_postgres_secret_id")
        require_setting("rancher_backend_workload_id")

        headers = {"Authorization": f"Bearer {settings.rancher_api_auth_token}"}

        click.echo(f"Getting current secret {settings.rancher_postgres_secret_id}")
        secret_url = (
            f"{settings.rancher_api_base_url}"
            f"/project/{settings.rancher_project_id}"
            f"/namespacedSecrets/{settings.rancher_postgres_secret_id}"
        )
        response = requests.get(secret_url, headers=headers)
        response.raise_for_status()
        current = response.json()
        update = {
            "data": {
                "INGEST_URI": current["data"]["POSTGRES_URI"],
                "POSTGRES_PASSWORD": current["data"]["POSTGRES_PASSWORD"],
                "POSTGRES_URI": current["data"]["INGEST_URI"],
            }
        }

        click.echo(f"Updating secret {settings.rancher_postgres_secret_id}")
        response = requests.put(secret_url, headers=headers, json=update)
        response.raise_for_status()

        click.echo(f"Redeploying workload {settings.rancher_backend_workload_id}")
        response = requests.post(
            f"{settings.rancher_api_base_url}"
            f"/project/{settings.rancher_project_id}"
            f"/workloads/{settings.rancher_backend_workload_id}?action=redeploy",
            headers=headers,
        )
        response.raise_for_status()

        response.raise_for_status()
        click.echo("Done")

    # If the user wants to swap secrets on Google Secret Manager, do it now.
    if swap_google_secrets:
        click.echo("Swapping secrets on Google Secret Manager")

        # TODO: Move this validation to the top of the ingest function so we fail early.
        def require_setting(name: str):
            if not getattr(settings, name, None):
                raise ValueError(f"{name} must be set to use --swap-google-secrets")

        require_setting("gcp_project_id")
        require_setting("gcp_primary_postgres_uri_secret_id")
        require_setting("gcp_secondary_postgres_uri_secret_id")

        # Note: We already validated these things above, but Pylance can't tell...
        #       ...which I think is the case because that validation happened within
        #       a different `if` block. So, we assert here to appease Pylance.
        assert settings.gcp_project_id is not None
        assert settings.gcp_primary_postgres_uri_secret_id is not None
        assert settings.gcp_secondary_postgres_uri_secret_id is not None

        # Swap the secret values.
        swap_gcp_secret_values(
            gcp_project_id=settings.gcp_project_id,
            secret_a_id=settings.gcp_primary_postgres_uri_secret_id,
            secret_b_id=settings.gcp_secondary_postgres_uri_secret_id,
        )

        click.echo("Done")

    # Calculate the total duration of this ingest (in minutes).
    ingest_end_datetime = datetime.datetime.now(datetime.timezone.utc)
    ingest_duration: datetime.timedelta = ingest_end_datetime - ingest_start_datetime
    ingest_duration_minutes = math.floor(ingest_duration.total_seconds() / 60)

    # Send a Slack message announcing that this ingest is done.
    send_slack_message(
        f"Ingest *finished successfully* in _{ingest_duration_minutes} minutes_.\n"
        f"• Start time: `{ingest_start_datetime_str}`\n"
        f"• MongoDB host: `{settings.mongo_host}`"
    )


@cli.command()
@click.option("--print-sql", is_flag=True, default=False)
@click.argument("script", required=False, type=click.Path(exists=True, dir_okay=False))
def shell(print_sql: bool, script: Optional[Path]):
    from IPython import start_ipython
    from traitlets.config import Config

    imports = [
        "from sqlalchmy import select",
        "from nmdc_server.config import settings",
        "from nmdc_server.database import SessionLocal, SessionLocalIngest",
        "from nmdc_server.models import "
        "Biosample, EnvoAncestor, EnvoTerm, EnvoTree, OmicsProcessing, Study",
        "from nmdc_server.query import "
        "SimpleConditionSchema, Operation, BiosampleQuerySchema, StudyQuerySchema",
    ]

    print("The following are auto-imported:")
    for line in imports:
        print(f"\033[1;32m{line}\033[0;0m")

    exec_lines = ["%autoreload 2"] + imports

    if print_sql:
        exec_lines.append("settings.print_sql = True")
        print("SQL debugging is ON")

    exec_lines.append("import os")
    exec_lines.append("from nmdc_server.app import create_app")
    exec_lines.append("app = create_app(env=os.environ.copy())")

    c = Config()
    c.InteractiveShellApp.exec_lines = exec_lines
    c.InteractiveShellApp.extensions = ["autoreload"]

    if script:
        c.InteractiveShellApp.file_to_run = script

    start_ipython(argv=[], config=c)


@cli.command()
@click.option("-u", "--user", help="NERSC username", default=os.getenv("USER"), show_default=True)
@click.option("-h", "--host", help="NERSC host", default="dtn01.nersc.gov", show_default=True)
@click.option("--list-backups", is_flag=True, help="Only list available backup filenames")
@click.option(
    "-f",
    "--backup-file",
    help=(
        "Filename in NERSC's backup directory to load. "
        "If not provided, the latest backup will be loaded."
    ),
)
@click.option(
    "-k",
    "--key-file",
    default="/tmp/nersc",
    show_default=True,
    help="Path to NERSC SSH key file within Docker container. Use if not using standard mounting.",
)
def load_db(key_file, user, host, list_backups, backup_file):
    """Load a local database from a production backup on NERSC."""
    pgdump_dir = "/global/cfs/cdirs/m3408/pgdump"

    if list_backups or not backup_file:
        click.echo("Finding latest production backups...")
        proc = subprocess.run(
            [
                "ssh",
                "-i",
                key_file,
                "-o",
                "StrictHostKeyChecking=no",
                f"{user}@{host}",
                f'find {pgdump_dir} -type f -iname "*pg_main-prod*.dump" -printf "%f\n"',
            ],
            capture_output=True,
            encoding="utf-8",
        )
        if proc.returncode != 0:
            click.echo("Error finding backups:")
            print(proc.stderr)
            sys.exit(1)

        dumps = sorted(proc.stdout.splitlines())
        if list_backups:
            click.echo("Available backups:")
            for dump in dumps:
                click.echo(dump)
            return

        if not dumps:
            click.echo("No backups found")
            sys.exit(1)

        backup_file = dumps[-1]

    if not (Path(os.getcwd()) / backup_file).exists():
        click.echo(f"Downloading {backup_file}...")
        subprocess.run(
            ["scp", "-i", key_file, f"{user}@{host}:{pgdump_dir}/{backup_file}", "."],
            check=True,
            encoding="utf-8",
        )

    click.echo(f"Restoring from {backup_file}...")
    # Use `Popen.communicate()` instead of `run()` to avoid buffering output
    open_proc = subprocess.Popen(
        [
            "pg_restore",
            "--dbname",
            settings.current_db_uri,
            "--clean",
            "--if-exists",
            "--verbose",
            "--single-transaction",
            backup_file,
        ],
        stdout=sys.stdout,
        stderr=sys.stderr,
        encoding="utf-8",
    )
    open_proc.communicate()
    if open_proc.returncode != 0:
        sys.exit(1)

    click.secho(f"\nSuccessfully loaded {settings.current_db_uri}", fg="green")


@cli.command()
@click.option("--remove-existing", is_flag=True, default=False)
def generate_static_files(remove_existing):
    click.echo("Generating static files...")
    static_path = initialize_static_directory(remove_existing=remove_existing)
    click.echo("Generating submission schema files...")
    generate_submission_schema_files(directory=static_path)
    click.echo("Done generating static files.")


@cli.group(name="storage")
def storage_group():
    """Commands for managing storage buckets and objects."""
    pass


@storage_group.command()
def init():
    """Ensure that the storage buckets exist."""
    for bucket_name in BucketName:
        click.echo(f"Ensuring bucket '{bucket_name}' exists")
        bucket = storage.get_bucket(bucket_name)
        if bucket.exists():
            click.echo(f"Bucket '{bucket_name}' already exists")
        elif settings.gcs_use_fake:
            click.echo(f"Creating bucket '{bucket_name}'")
            bucket.create()
        else:
            raise RuntimeError(
                f"Failed to ensure bucket '{bucket_name}' exists. "
                f"This bucket may need to be created manually in the cloud storage provider."
            )


@storage_group.command()
@click.option("--dry-run", is_flag=True, default=False)
def vacuum(dry_run: bool):
    """Vacuum the storage buckets to remove objects not referenced in the database."""
    for bucket_name in BucketName:
        click.echo(f"Vacuuming bucket '{bucket_name}'")
        if bucket_name == BucketName.SUBMISSION_IMAGES:
            with SessionLocal() as db:
                bucket = storage.get_bucket(bucket_name)
                for blob in bucket.list_blobs(prefix=settings.gcs_object_name_prefix):
                    db_image = db.get(SubmissionImagesObject, blob.name)
                    if not db_image:
                        click.echo(f"Deleting blob '{blob.name}' from bucket '{bucket_name}'")
                        if not dry_run:
                            blob.delete()


if __name__ == "__main__":
    cli()
