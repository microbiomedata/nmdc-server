from datetime import datetime
import json
import logging
import re
from typing import Any, Dict

from pydantic import root_validator, validator
from pymongo.cursor import Cursor
from sqlalchemy.orm import Session

from nmdc_server import models
from nmdc_server.ingest.common import extract_extras, extract_value
from nmdc_server.ingest.errors import errors, missing as missing_
from nmdc_server.ingest.study import study_ids
from nmdc_server.schemas import ProjectCreate

logger = logging.getLogger(__name__)
date_fmt = re.compile(r"\d\d-[A-Z]+-\d\d \d\d\.\d\d\.\d\d\.\d+ [AP]M")


class Project(ProjectCreate):
    _extract_value = validator("*", pre=True, allow_reuse=True)(extract_value)

    @root_validator(pre=True)
    def extract_extras(cls, values):
        return extract_extras(cls, values)

    @validator("add_date", "mod_date", pre=True)
    def coerce_date(cls, v):
        if isinstance(v, str) and date_fmt.match(v):
            return datetime.strptime(v, "%d-%b-%y %I.%M.%S.%f000 %p").isoformat()


def load_project(db: Session, obj: Dict[str, Any]):
    obj["biosample_id"] = obj.pop("has_input", [None])[0]
    data_objects = obj.pop("has_output", [])
    obj["study_id"] = obj.pop("part_of", [None])[0]
    if obj["study_id"] not in study_ids:
        return

    if obj["biosample_id"] and db.query(models.Biosample).get(obj["biosample_id"]) is None:
        logger.warn(f"Unknown biosample {obj['biosample_id']}")
        missing_["biosample"].add(obj.pop("biosample_id"))

    project = models.Project(**Project(**obj).dict())

    for data_object_id in data_objects:
        data_object = db.query(models.DataObject).get(data_object_id)
        if data_object is None:
            logger.warning(f"Unknown data object {data_object_id}")
            missing_["data_object"].add(data_object_id)
            continue

        data_object.project = project
        db.add(data_object)
        project.outputs.append(data_object)  # type: ignore

    db.add(project)


def load(db: Session, cursor: Cursor):
    for obj in cursor:
        try:
            load_project(db, obj)
        except Exception:
            logger.error("Error parsing project:")
            logger.error(json.dumps(obj, indent=2, default=str))
            errors["project"].add(obj["id"])
    db.commit()
