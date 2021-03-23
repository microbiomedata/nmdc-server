from pathlib import Path

from alembic import command
from alembic.config import Config

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
    database._engine = None
    with create_session() as db:
        engine = db.bind
        metadata.create_all(engine)
        alembic_cfg = Config(str(HERE / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(HERE / "migrations"))
        alembic_cfg.set_main_option("sqlalchemy.url", database_uri)
        alembic_cfg.attributes["configure_logger"] = False
        if command.current(alembic_cfg) is None:
            command.stamp(alembic_cfg, "head")
        else:
            command.upgrade(alembic_cfg, "head")
    database._engine = None


@celery_app.task
def ingest():
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
                for row in db.execute("select truncate_tables()"):
                    pass
                load(db)
                for row in prod_db.query(models.FileDownload):
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
