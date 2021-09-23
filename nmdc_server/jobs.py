import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext

from nmdc_server import database, models
from nmdc_server.celery_config import celery_app
from nmdc_server.config import settings
from nmdc_server.ingest.all import load
from nmdc_server.ingest.lock import ingest_lock

HERE = Path(__file__).parent


@celery_app.task
def ping():
    return True


def migrate(ingest_db: bool = False):
    """Update the database to the latest HEAD.

    This function will also create the schema if necessary.
    """
    if ingest_db:
        database_uri = settings.ingest_database_uri
        engine = database.engine_ingest
        session_maker = database.SessionLocalIngest
    else:
        database_uri = settings.current_db_uri
        engine = database.engine
        session_maker = database.SessionLocal

    with session_maker() as db:
        alembic_cfg = Config(str(HERE / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(HERE / "migrations"))
        alembic_cfg.set_main_option("sqlalchemy.url", database_uri)
        alembic_cfg.attributes["configure_logger"] = True

        with db.connection() as conn:
            context = MigrationContext.configure(conn)
            head = context.get_current_revision()
            if head is None:
                database.metadata.create_all(bind=engine)
                command.stamp(alembic_cfg, "head")
            else:
                command.upgrade(alembic_cfg, "head")


@celery_app.task
def ingest():
    """Truncate database and ingest all data from the mongo source."""
    logger = logging.getLogger()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger.setLevel(logging.INFO)

    with database.SessionLocalIngest() as ingest_db:
        try:
            ingest_db.execute("select truncate_tables()").all()
        except Exception:
            # eat the exception, we'll truncate after migration
            ingest_db.rollback()

    migrate(ingest_db=True)

    with database.SessionLocalIngest() as ingest_db, database.SessionLocal() as prod_db:
        with ingest_lock(prod_db):
            try:
                ingest_db.execute("select truncate_tables()").all()

                # ingest data
                load(ingest_db)

                # copy persistent data from the production db to the ingest db
                for row in prod_db.query(models.FileDownload):
                    ingest_db.merge(row)
                for row in prod_db.query(models.BulkDownload):
                    ingest_db.merge(row)
                for row in prod_db.query(models.BulkDownloadDataObject):
                    ingest_db.merge(row)
                ingest_db.commit()
            except Exception:
                ingest_db.rollback()
                raise

    populate_gene_functions()


@celery_app.task
def populate_gene_functions():
    """Populate denormalized gene function tables."""
    with database.SessionLocalIngest() as ingest_db:
        with ingest_db.begin():
            models.MGAGeneFunctionAggregation.populate(ingest_db)
            models.MetaPGeneFunctionAggregation.populate(ingest_db)
