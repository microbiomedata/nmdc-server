from contextlib import contextmanager

from sqlalchemy.orm import Session

from nmdc_server.models import IngestLock


class IngestInProgress(Exception):
    def __init__(self, created):
        self.created = created


# This context manager acts as a mutex to avoid multiple simultaneous ingest jobs.
@contextmanager
def ingest_lock(db: Session):
    lock = db.query(IngestLock).first()
    if lock:
        raise IngestInProgress(lock.started)
    lock = IngestLock()
    db.add(lock)
    db.commit()
    try:
        yield lock
    except Exception:
        db.rollback()
        raise
    finally:
        db.delete(lock)
        db.commit()
