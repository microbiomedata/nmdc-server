import logging
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

    jobs.do_ingest(function_limit, skip_annotation)

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

    # Post a message to Slack if a Slack webhook URL is defined.
    # Reference: https://api.slack.com/messaging/webhooks#posting_with_webhooks
    if settings.slack_webhook_url_for_ingester not in [None, ""]:
        click.echo("Posting message to Slack.")
        response = requests.post(
            settings.slack_webhook_url_for_ingester,
            json={"text": "Ingest is done."},
            headers={"Content-type": "application/json"},
        )
        # Note: We currently consider the posting of a Slack message to be a "nice
        #       to have" as opposed to a "must have." So, if it happens to fail,
        #       we just echo an error message instead of `raise`-ing an exception.
        if response.status_code != 200:
            click.echo("Failed to post message to Slack.", err=True)


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


if __name__ == "__main__":
    cli()
