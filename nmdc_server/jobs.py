import logging
from pathlib import Path

from nmdc_server import database, models
from nmdc_server.celery_config import celery_app
from nmdc_server.ingest.all import load
from nmdc_server.logger import get_logger

HERE = Path(__file__).parent


@celery_app.task
def ping():
    return True


@celery_app.task
def ingest(function_limit=None, skip_annotation=False):
    """Clear database and ingest all data from the mongo source."""
    logger = get_logger(__name__)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger.setLevel(logging.INFO)

    with database.SessionLocal() as db:
        database.get_ingest_lock(db)
        database.clear_tables(db)
        logger.info(f"Load with function_limit={function_limit}, skip_annotation={skip_annotation}")
        load(db, function_limit=function_limit, skip_annotation=skip_annotation)

        populate_gene_functions()


@celery_app.task
def populate_gene_functions():
    """Populate denormalized gene function tables."""
    with database.SessionLocal() as db:
        database.get_ingest_lock(db)
        with db.begin():
            models.MGAGeneFunctionAggregation.populate(db)
            models.MetaPGeneFunctionAggregation.populate(db)
