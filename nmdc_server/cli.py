import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
import click

from nmdc_server import database, models  # noqa: ensure all models are initialized
from nmdc_server.config import Settings
from nmdc_server.database import create_session, metadata
from nmdc_server.ingest.all import load

HERE = Path(__file__).parent


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
    with create_session() as db:
        engine = db.bind
        metadata.create_all(engine)
        alembic_cfg = Config(str(HERE / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(HERE / "migrations"))
        alembic_cfg.set_main_option("sqlalchemy.url", obj["database_uri"])
        alembic_cfg.attributes["configure_logger"] = False
        if command.current(alembic_cfg) is None:
            command.stamp(alembic_cfg, "head")
        else:
            # TODO: Figure out why this doesn't work
            # command.upgrade(alembic_cfg, "head")
            pass


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
def ingest(verbose):
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
        load(db)
