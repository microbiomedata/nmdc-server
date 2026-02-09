from pathlib import Path
from typing import Dict

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.orm import lazyload

from nmdc_server import database, models
from nmdc_server.config import settings
from nmdc_server.ingest.all import load
from nmdc_server.ingest.common import (
    ETLReport,
    maybe_merge_download_artifact,
    merge_download_artifact,
)
from nmdc_server.ingest.lock import ingest_lock
from nmdc_server.logger import get_logger

HERE = Path(__file__).parent

logger = get_logger(__name__)


def update_nmdc_functions():
    """Update NMDC custom functions for both databases."""
    for db_info in [(database.SessionLocal, "active"), (database.SessionLocalIngest, "ingest")]:
        db_to_update, db_type = db_info
        with db_to_update() as db:
            logger.info(f"Updating NMDC functions for the {db_type} database.")
            db.execute(database.update_nmdc_functions_sql)
            db.commit()


def migrate(ingest_db: bool = False):
    """Update the database to the latest HEAD.

    This function will also create the schema if necessary.
    """
    update_nmdc_functions()
    if ingest_db:
        database_uri = settings.ingest_database_uri
        session_maker = database.SessionLocalIngest
    else:
        database_uri = settings.current_db_uri
        session_maker = database.SessionLocal

    with session_maker.begin():  # type: ignore
        alembic_cfg = Config(str(HERE / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(HERE / "migrations"))
        alembic_cfg.set_main_option("sqlalchemy.url", database_uri)
        alembic_cfg.attributes["configure_logger"] = True
        command.upgrade(alembic_cfg, "head")


def do_ingest(function_limit, skip_annotation) -> Dict[str, ETLReport]:
    r"""
    Note: The `ingest_lock()` function invoked within this function may raise an exception.
          Since such an exception will not be caught within this function, it will propagate
          up to the code that _invoked_ this function.

    Returns a dictionary containing reports about various parts of the ingest process.
    """

    with database.SessionLocalIngest() as ingest_db:
        try:
            ingest_db.execute(text("select truncate_tables()")).all()
        except Exception:
            # eat the exception, we'll truncate after migration
            ingest_db.rollback()

    migrate(ingest_db=True)

    with database.SessionLocalIngest() as ingest_db, database.SessionLocal() as prod_db:
        with ingest_lock(prod_db):
            ingest_db.execute(text("select truncate_tables()")).all()

            # Ingest data from the MongoDB database into the "ingest" Postgres database.
            logger.info(
                f"Load with function_limit={function_limit}, skip_annotation={skip_annotation}"
            )
            reports = load(
                ingest_db, function_limit=function_limit, skip_annotation=skip_annotation
            )

            # Copy "dependent" data from the "portal" database into the "ingest" database.
            #
            # Note: This set of data depends upon the script having already ingested data from
            #       the MongoDB database (this data has some foreign keys pointing to that data).
            #
            logger.info("Copying dependent data from the portal database to the ingest database.")
            logger.info("Merging download-related data")
            maybe_merge_download_artifact(ingest_db, prod_db.query(models.FileDownload))
            maybe_merge_download_artifact(ingest_db, prod_db.query(models.BulkDownload))
            maybe_merge_download_artifact(
                ingest_db,
                prod_db.query(models.BulkDownloadDataObject).options(
                    lazyload(models.BulkDownloadDataObject.data_object)
                ),
            )

            # Copy "independent" data from the "portal" database into the "ingest" database.
            #
            # Note: This set of data does _not_ depend upon the script having already ingested data
            #       from the MongoDB database (this data has no foreign keys pointing to that data).
            #       So, we could copy this data earlier in the ingest process. The reason we do it
            #       this late is to minimize the amount of time between when we copy submission data
            #       and when we promote the "ingest" database into the new "portal" database, to
            #       reduce the opportunity for submission changes to end up in the wrong database.
            #
            logger.info("Copying independent data from the portal database to the ingest database.")
            logger.info("Merging auth-related data")
            merge_download_artifact(ingest_db, prod_db.query(models.User))
            merge_download_artifact(ingest_db, prod_db.query(models.AuthorizationCode))
            merge_download_artifact(ingest_db, prod_db.query(models.InvalidatedToken))
            logger.info("Merging submission-related data")
            merge_download_artifact(ingest_db, prod_db.query(models.SubmissionImagesObject))
            merge_download_artifact(ingest_db, prod_db.query(models.SubmissionMetadata))
            merge_download_artifact(ingest_db, prod_db.query(models.SubmissionRole))

    logger.info("Ingest finished successfully")

    return reports
