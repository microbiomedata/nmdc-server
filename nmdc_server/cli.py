import logging

import click

from nmdc_server import database, jobs
from nmdc_server.config import Settings
from nmdc_server.database import create_session
from nmdc_server.ingest import errors
from nmdc_server.ingest.all import load


@click.group()
@click.option("--testing/--no-testing", help="Use the testing database")
@click.pass_context
def cli(ctx, testing):
    database.testing = testing
    settings = Settings()
    ctx.obj = {
        "testing": testing,
        "settings": settings,
        "database_uri": settings.testing_database_uri if testing else settings.database_uri,
    }


@cli.command()
@click.pass_obj
def migrate(obj):
    """Upgrade the database schema."""
    jobs.migrate(obj["database_uri"])


@cli.command()
def truncate():
    """Remove all existing data."""
    with create_session() as db:
        try:
            for row in db.execute("select truncate_tables()"):
                pass
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
def ingest(verbose, function_limit):
    """Ingest the latest data from mongo."""
    level = logging.WARN
    if verbose == 1:
        level = logging.INFO
    elif verbose > 1:
        level = logging.DEBUG
    logger = logging.getLogger()
    logging.basicConfig(
        level=level,
        format="%(message)s",
    )
    logger.setLevel(logging.INFO)
    with create_session() as db:
        load(db, function_limit=function_limit)

    for m, s in errors.missing.items():
        click.echo(f"missing {m}:")
        for id in s:
            click.echo(id)

    for m, s in errors.errors.items():
        click.echo(f"errors {m}:")
        for id in s:
            click.echo(id)
