from nmdc_server.celery import celery_app
from nmdc_server.database import create_session
from nmdc_server.ingest.all import load
from nmdc_server.ingest.lock import ingest_lock


@celery_app.task
def ping():
    return True


@celery_app.task
def ingest():
    with create_session() as db:
        with ingest_lock(db):
            try:
                for row in db.execute("select truncate_tables()"):
                    pass
                load(db)
                db.commit()
            except Exception:
                db.rollback()
                raise
