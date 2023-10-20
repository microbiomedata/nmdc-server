import logging
from pathlib import Path
from typing import Optional

import click

from nmdc_server import jobs, models
from nmdc_server.config import Settings, settings
from nmdc_server.database import SessionLocal, SessionLocalIngest
from nmdc_server.ingest import errors
from nmdc_server.ingest.all import load
from nmdc_server.ingest.common import maybe_merge_download_artifact
from nmdc_server.logger import get_logger


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
def ingest(verbose, function_limit, skip_annotation):
    """Ingest the latest data from mongo into the ingest database."""
    level = logging.WARN
    if verbose == 1:
        level = logging.INFO
    elif verbose > 1:
        level = logging.DEBUG
    logger = get_logger(__name__)
    logging.basicConfig(level=level, format="%(message)s")
    logger.setLevel(logging.INFO)
    jobs.migrate(ingest_db=True)
    with SessionLocalIngest() as ingest_db:
        load(ingest_db, function_limit=function_limit, skip_annotation=skip_annotation)
        if settings.current_db_uri != settings.ingest_database_uri:
            with SessionLocal() as prod_db:
                # copy persistent data from the production db to the ingest db
                maybe_merge_download_artifact(ingest_db, prod_db.query(models.FileDownload))
                maybe_merge_download_artifact(ingest_db, prod_db.query(models.BulkDownload))
                maybe_merge_download_artifact(
                    ingest_db, prod_db.query(models.BulkDownloadDataObject)
                )

    for m, s in errors.missing.items():
        click.echo(f"missing {m}:")
        for id in s:
            click.echo(id)

    for m, s in errors.errors.items():
        click.echo(f"errors {m}:")
        for id in s:
            click.echo(id)


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
