import logging
from pathlib import Path
from typing import Optional

import click

from nmdc_server import jobs
from nmdc_server.config import Settings
from nmdc_server.database import SessionLocal
from nmdc_server.ingest import errors
from nmdc_server.ingest.all import load


@click.group()
@click.pass_context
def cli(ctx):
    settings = Settings()
    if settings.environment == "testing":
        settings.database_uri = settings.testing_database_uri

    ctx.obj = {"settings": settings}


@cli.command()
@click.pass_obj
def migrate(obj):
    """Upgrade the database schema."""
    jobs.migrate(obj["settings"].database_uri)


@cli.command()
def truncate():
    """Remove all existing data."""
    with SessionLocal() as db:
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
    """Ingest the latest data from mongo."""
    level = logging.WARN
    if verbose == 1:
        level = logging.INFO
    elif verbose > 1:
        level = logging.DEBUG
    logger = logging.getLogger()
    logging.basicConfig(level=level, format="%(message)s")
    logger.setLevel(logging.INFO)

    with SessionLocal() as db:
        load(db, function_limit=function_limit, skip_annotation=skip_annotation)

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
        "from nmdc_server.database import SessionLocal",
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
