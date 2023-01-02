import logging
from pathlib import Path
from typing import Optional

import click
from alembic import command
from alembic.config import Config

from nmdc_server import database
from nmdc_server.config import settings
from nmdc_server.ingest import errors
from nmdc_server.ingest.all import load
from nmdc_server.logger import get_logger


@click.group()
@click.pass_context
def cli(ctx):
    if settings.environment == "testing":
        settings.database_uri = settings.testing_database_uri
    ctx.obj = {"settings": settings}


@cli.command()
def migrate():
    """Upgrade the database schema."""
    database_uri = settings.current_db_uri
    session_maker = database.SessionLocal

    with session_maker.begin() as db:  # type: ignore
        database.get_ingest_lock(db)
        alembic_cfg = Config(str(Path(__file__).parent / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(Path(__file__).parent / "migrations"))
        alembic_cfg.set_main_option("sqlalchemy.url", database_uri)
        alembic_cfg.attributes["configure_logger"] = True
        command.upgrade(alembic_cfg, "head")


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
    with database.SessionLocal() as db:
        with db.begin():
            database.get_ingest_lock(db)
            database.clear_tables(db)
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
