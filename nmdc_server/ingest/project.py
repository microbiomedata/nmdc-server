import logging
from typing import Any, Dict

from pydantic import root_validator, validator
from pymongo.cursor import Cursor
from sqlalchemy.orm import Session

from nmdc_server import models
from nmdc_server.ingest.common import extract_extras, extract_value
from nmdc_server.schemas import ProjectCreate

logger = logging.getLogger(__name__)


class Project(ProjectCreate):
    _extract_value = validator("*", pre=True, allow_reuse=True)(extract_value)

    @root_validator(pre=True)
    def extract_extras(cls, values):
        return extract_extras(cls, values)


def load_project(db: Session, obj: Dict[str, Any]):
    obj["biosample_id"] = obj.pop("has_input", [None])[0]
    data_objects = obj.pop("has_output", [])
    obj.pop("part_of", None)

    if obj["biosample_id"] and db.query(models.Biosample).get(obj["biosample_id"]) is None:
        logger.warn(f"Unknown biosample {obj['biosample_id']}")
        obj.pop("biosample_id")

    project = models.Project(**Project(**obj).dict())
    for data_object_id in data_objects:
        data_object = db.query(models.DataObject).get(data_object_id)
        if data_object is None:
            logger.warning(f"Unknown data object {data_object_id}")
            continue

        data_object.project = project
        db.add(data_object)
    db.add(project)


def load(db: Session, cursor: Cursor):
    for obj in cursor:
        load_project(db, obj)
    db.commit()
