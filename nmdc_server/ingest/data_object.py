from pymongo.cursor import Cursor
from sqlalchemy.orm import Session

from nmdc_server.models import DataObject


def load(db: Session, cursor: Cursor):
    for obj in cursor:
        obj.pop("_id")

        # TODO: Remove once the source data is fixed.
        url = obj.get("url", "")
        if url.startswith("https://data.microbiomedata.org") and not url.startswith(
            "https://data.microbiomedata.org/data"
        ):
            obj["url"] = url.replace(
                "https://data.microbiomedata.org", "https://data.microbiomedata.org/data"
            )

        db.add(DataObject(**obj))
