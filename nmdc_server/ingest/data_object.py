from typing import Any, Dict, List, Tuple

from pymongo.cursor import Cursor
from sqlalchemy.orm import Session

from nmdc_server.data_object_filters import get_local_data_url
from nmdc_server.ingest.logger import get_logger
from nmdc_server.models import DataObject
from nmdc_server.schemas import DataObjectCreate

file_type_map: Dict[str, Tuple[str, str]] = {}


def load(db: Session, cursor: Cursor, file_types: List[Dict[str, Any]]):
    logger = get_logger(__name__)
    fields = set(DataObjectCreate.__fields__.keys()) | {"data_object_type"}

    file_type_map = {f["id"]: (f["name"], f["description"]) for f in file_types}

    objects_without_type = 0

    for obj_ in cursor:
        obj = {key: obj_[key] for key in obj_.keys() & fields}

        # TODO: Remove once the source data is fixed.
        url = obj.get("url", "")
        if url and not get_local_data_url(url):
            logger.warning(
                f"Unknown url host '{url}', it need to be added to nginx config for bulk download"
            )
        if url.startswith("https://data.microbiomedata.org") and not url.startswith(
            "https://data.microbiomedata.org/data"
        ):
            obj["url"] = url.replace(
                "https://data.microbiomedata.org", "https://data.microbiomedata.org/data"
            )
        if "data_object_type" in obj:
            obj["file_type"], obj["file_type_description"] = file_type_map[
                obj.pop("data_object_type")
            ]
        else:
            objects_without_type += 1

        db.add(DataObject(**obj))

    if objects_without_type:
        logger.error(f"Encountered {objects_without_type} objects without data_object_type")
