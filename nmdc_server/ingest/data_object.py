from pymongo.cursor import Cursor
from sqlalchemy.orm import Session

from nmdc_server.models import DataObject
from nmdc_server.schemas import DataObjectCreate


def load(db: Session, cursor: Cursor):
    fields = set(DataObjectCreate.__fields__.keys())
    for obj_ in cursor:
        obj = {key: obj_[key] for key in obj_.keys() & fields}

        # TODO: Remove once the source data is fixed.
        url = obj.get("url", "")
        if url.startswith("https://data.microbiomedata.org") and not url.startswith(
            "https://data.microbiomedata.org/data"
        ):
            obj["url"] = url.replace(
                "https://data.microbiomedata.org", "https://data.microbiomedata.org/data"
            )

        db.add(DataObject(**obj))
