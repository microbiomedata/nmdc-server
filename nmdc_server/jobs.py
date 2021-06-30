import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext

from nmdc_server import database, models
from nmdc_server.celery import celery_app
from nmdc_server.config import settings
from nmdc_server.database import create_engine, create_session, metadata
from nmdc_server.ingest.all import load
from nmdc_server.ingest.lock import ingest_lock


HERE = Path(__file__).parent


@celery_app.task
def ping():
    return True


def migrate(database_uri):
    """Update the database to the latest HEAD.

    This function will also create the schema if necessary.
    """
    database._engine = None
    with create_session() as db:
        engine = db.bind
        alembic_cfg = Config(str(HERE / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(HERE / "migrations"))
        alembic_cfg.set_main_option("sqlalchemy.url", database_uri)
        alembic_cfg.attributes["configure_logger"] = True

        context = MigrationContext.configure(db.connection())
        head = context.get_current_revision()
        if head is None:
            metadata.create_all(engine)
            command.stamp(alembic_cfg, "head")
        else:
            command.upgrade(alembic_cfg, "head")
    database._engine = None


@celery_app.task
def ingest():
    """Truncate database and ingest all data from the mongo source."""
    logger = logging.getLogger()
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )
    logger.setLevel(logging.INFO)

    database._engine = None
    database.ingest = False
    prod_engine = create_engine()

    database._engine = None
    database.ingest = True
    with create_session() as db:
        try:
            for row in db.execute("select truncate_tables()"):
                pass
        except Exception:
            db.rollback()

    migrate(settings.ingest_database_uri)

    with create_session() as db, create_session(prod_engine) as prod_db:
        with ingest_lock(db):
            try:
                # truncate tables
                for row in db.execute("select truncate_tables()"):
                    pass

                # ingest data
                load(db)

                # copy persistent data from the production database over to the
                # ingest database
                for row in prod_db.query(models.FileDownload):
                    db.merge(row)
                for row in prod_db.query(models.BulkDownload):
                    db.merge(row)
                for row in prod_db.query(models.BulkDownloadDataObject):
                    db.merge(row)
                db.commit()
            except Exception:
                db.rollback()
                raise
    database._engine = None
    database.ingest = False

    populate_gene_functions()


@celery_app.task
def populate_gene_functions():
    """Populate denormalized gene function tables."""
    database._engine = None
    database.ingest = True
    with create_session() as db:
        with ingest_lock(db):
            try:
                models.MGAGeneFunctionAggregation.populate(db)
                models.MetaPGeneFunctionAggregation.populate(db)
                db.commit()
            except Exception:
                db.rollback()
                raise
    database._engine = None
    database.ingest = False
