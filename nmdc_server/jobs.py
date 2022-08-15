import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

from nmdc_server import database, models
from nmdc_server.celery_config import celery_app
from nmdc_server.config import settings
from nmdc_server.ingest.all import load
from nmdc_server.ingest.common import maybe_merge_download_artifact, merge_download_artifact
from nmdc_server.ingest.lock import ingest_lock
from nmdc_server.logger import get_logger

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
        session_maker = database.SessionLocalIngest
    else:
        database_uri = settings.current_db_uri
        session_maker = database.SessionLocal

    with session_maker() as db:
        alembic_cfg = Config(str(HERE / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(HERE / "migrations"))
        alembic_cfg.set_main_option("sqlalchemy.url", database_uri)
        alembic_cfg.attributes["configure_logger"] = True
        command.upgrade(alembic_cfg, "head")


@celery_app.task
def ingest(function_limit=None, skip_annotation=False):
    """Truncate database and ingest all data from the mongo source."""
    logger = get_logger(__name__)
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
            ingest_db.execute("select truncate_tables()").all()

            # Copy persistent data that does not depend on ingest FK
            merge_download_artifact(ingest_db, prod_db.query(models.User))
            merge_download_artifact(ingest_db, prod_db.query(models.SubmissionMetadata))

            # ingest data
            logger.info(
                f"Load with function_limit={function_limit}, skip_annotation={skip_annotation}"
            )
            load(ingest_db, function_limit=function_limit, skip_annotation=skip_annotation)

            # copy persistent data from the production db to the ingest db
            maybe_merge_download_artifact(ingest_db, prod_db.query(models.FileDownload))
            maybe_merge_download_artifact(ingest_db, prod_db.query(models.BulkDownload))
            maybe_merge_download_artifact(ingest_db, prod_db.query(models.BulkDownloadDataObject))
            populate_gene_functions()


@celery_app.task
def populate_gene_functions():
    """Populate denormalized gene function tables."""
    with database.SessionLocalIngest() as ingest_db:
        with ingest_db.begin():
            models.MGAGeneFunctionAggregation.populate(ingest_db)
            models.MetaPGeneFunctionAggregation.populate(ingest_db)
