from typing import Any, Dict, List, Tuple

from nmdc_schema.nmdc_data import get_nmdc_file_type_enums
from pymongo.cursor import Cursor
from sqlalchemy.orm import Session

from nmdc_server.logger import get_logger
from nmdc_server.models import DataObject, OmicsProcessing
from nmdc_server.schemas import DataObjectCreate

file_type_map: Dict[str, Tuple[str, str]] = {}


def load(db: Session, cursor: Cursor, file_types: List[Dict[str, Any]]):
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

    if objects_without_type:
        logger.error(f"Encountered {objects_without_type} objects without data_object_type")


def update_data_generation_relation(db: Session, cursor: Cursor):
    """
    Update DataObject's omics_processing_id FK.

    This should run after ingesting all data objects and data generations (omics processing).
    """
    for data_object in cursor:
        id = data_object["id"]
        was_generated_by = data_object.pop("was_generated_by", None)
        if not was_generated_by:
            continue
        # Mypy does not like db.get, and reports that "Session" has no attribute "get."
        # See https://docs.sqlalchemy.org/en/14/orm/session_basics.html#get-by-primary-key
        data_generation = db.get(OmicsProcessing, was_generated_by)  # type: ignore
        row = db.get(DataObject, id)  # type: ignore
        if row and data_generation:
            row.omics_processing_id = was_generated_by
            db.add(row)
