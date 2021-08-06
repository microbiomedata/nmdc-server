import logging
from typing import List

import click
from sqlalchemy.sql import text as sa_text

from nmdc_server import jobs
from nmdc_server.config import Settings
from nmdc_server.database import create_session
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
@click.argument("tables", type=click.STRING, nargs=-1, default=None)
def truncate(tables: List[str]):
    """Remove all existing data."""
    with create_session() as db:
        if len(tables) > 0:
            for table in tables:
                db.execute(sa_text(f"TRUNCATE TABLE {table}"))
                db.commit()
        else:
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
@click.option("--cheap-only", is_flag=True, default=False)
def ingest(verbose, function_limit, cheap_only):
    """Ingest the latest data from mongo."""
    level = logging.WARN
    if verbose == 1:
        level = logging.INFO
    elif verbose > 1:
        level = logging.DEBUG
    logger = logging.getLogger()
    logging.basicConfig(level=level, format="%(message)s")
    logger.setLevel(logging.INFO)

    with create_session() as db:
        load(db, function_limit=function_limit, cheap_only=cheap_only)

    for m, s in errors.missing.items():
        click.echo(f"missing {m}:")
        for id in s:
            click.echo(id)

    for m, s in errors.errors.items():
        click.echo(f"errors {m}:")
        for id in s:
            click.echo(id)
