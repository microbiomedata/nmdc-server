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

from nmdc_server import jobs
from nmdc_server.config import Settings
from nmdc_server.database import SessionLocalIngest
from nmdc_server.ingest import errors
from nmdc_server.static_files import generate_submission_schema_files, initialize_static_directory


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
    settings = Settings()
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
    settings = Settings()
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
            db.execute("select truncate_tables()").all()
            db.commit()
        except Exception:
            db.rollback()
            db.execute(
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
            db.commit()


@cli.command()
@click.option("-v", "--verbose", count=True)
@click.option("--function-limit", type=click.INT, default=100)
@click.option("--skip-annotation", is_flag=True, default=False)
@click.option("--swap-rancher-secrets", is_flag=True, default=False)
def ingest(verbose, function_limit, skip_annotation, swap_rancher_secrets):
    """Ingest the latest data from mongo into the ingest database."""
    settings = Settings()

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

        def require_setting(name: str):
            if not getattr(settings, name, None):
                raise ValueError(f"{name} must be set to use --swap-rancher-secrets")

        require_setting("rancher_api_base_url")
        require_setting("rancher_api_auth_token")
        require_setting("rancher_project_id")
        require_setting("rancher_postgres_secret_id")
        require_setting("rancher_backend_workload_id")
        require_setting("rancher_worker_workload_id")

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

        click.echo(f"Redeploying workload {settings.rancher_worker_workload_id}")
        response = requests.post(
            f"{settings.rancher_api_base_url}"
            f"/project/{settings.rancher_project_id}"
            f"/workloads/{settings.rancher_worker_workload_id}?action=redeploy",
            headers=headers,
        )
        response.raise_for_status()
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
        "from nmdc_server.config import settings",
        "from nmdc_server.database import SessionLocal, SessionLocalIngest",
        "from nmdc_server.models import "
        "Biosample, EnvoAncestor, EnvoTerm, EnvoTree, OmicsProcessing, Study",
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
    settings = Settings()
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


if __name__ == "__main__":
    cli()
