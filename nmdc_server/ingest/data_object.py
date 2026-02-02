from typing import Any, Dict, List, Tuple

from nmdc_schema.nmdc_data import get_nmdc_file_type_enums
from pymongo.cursor import Cursor
from sqlalchemy.orm import Session

from nmdc_server.ingest.common import ETLReport
from nmdc_server.logger import get_logger
from nmdc_server.models import DataObject
from nmdc_server.schemas import DataObjectCreate

file_type_map: Dict[str, Tuple[str, str]] = {}


def load(db: Session, cursor: Cursor, file_types: List[Dict[str, Any]]) -> ETLReport:

    # Initialize the report we will return.
    report = ETLReport(plural_subject="DataObjects")

    logger = get_logger(__name__)
    fields = set(DataObjectCreate.model_fields.keys()) | {"data_object_type"}
    file_type_map: Dict[str, Tuple[str, str]] = {}

    # Load descriptors from mongo collection.
    # TODO: Remove this section once all data_object_type have been converted
    for val in file_types:
        file_type_map[val["id"]] = (val["name"], val["description"])
    # Load additional descriptors from schema
    for val in get_nmdc_file_type_enums():
        file_type_map[val["name"]] = (val["name"], val["description"])

    objects_without_type = 0

    for obj_ in cursor:
        report.num_extracted += 1

        obj = {key: obj_[key] for key in obj_.keys() & fields}

        if "data_object_type" in obj:
            enum_type = obj.pop("data_object_type")
            type_tuple = file_type_map.get(enum_type, None)
            if type_tuple:
                obj["file_type"], obj["file_type_description"] = type_tuple
            else:
                logger.warning(f"Unknown data_object_type {enum_type} for data_object {obj['id']}")
        else:
            objects_without_type += 1

        db.add(DataObject(**obj))
        report.num_loaded += 1

    if objects_without_type:
        logger.error(f"Encountered {objects_without_type} objects without data_object_type")

    return report
