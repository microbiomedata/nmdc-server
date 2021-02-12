from datetime import datetime
import json
import logging
import re
from typing import Any, Dict

from pydantic import root_validator, validator
from pymongo.collection import Collection
from pymongo.cursor import Cursor
from sqlalchemy.orm import Session

from nmdc_server import models
from nmdc_server.ingest.common import extract_extras, extract_value
from nmdc_server.ingest.study import study_ids
from nmdc_server.schemas import BiosampleCreate

logger = logging.getLogger(__name__)
date_fmt = re.compile(r"\d\d-[A-Z]+-\d\d \d\d\.\d\d\.\d\d\.\d+ [AP]M")


class Biosample(BiosampleCreate):
    _extract_value = validator("*", pre=True, allow_reuse=True)(extract_value)

    @root_validator(pre=True)
    def extract_extras(cls, values):
        if "lat_lon" in values:
            lat, lon = values.pop("lat_lon")["has_raw_value"].split(" ")
            values["latitude"] = float(lat)
            values["longitude"] = float(lon)

        return extract_extras(cls, values)

    @validator("depth", pre=True)
    def normalize_depth(cls, value):
        value = extract_value(value)
        if isinstance(value, str):
            return float(value.split(" ")[0])
        return value

    @validator("add_date", "mod_date", pre=True)
    def coerce_date(cls, v):
        if isinstance(v, str) and date_fmt.match(v):
            return datetime.strptime(v, "%d-%b-%y %I.%M.%S.%f000 %p").isoformat()


def load_biosample(db: Session, obj: Dict[str, Any], omics_processing: Collection):
    invalid = {"has_raw_value": ""}
    env_broad_scale = db.query(models.EnvoTerm).get(
        obj.pop("env_broad_scale", invalid)["has_raw_value"]
    )
    env_local_scale = db.query(models.EnvoTerm).get(
        obj.pop("env_local_scale", invalid)["has_raw_value"]
    )
    env_medium = db.query(models.EnvoTerm).get(obj.pop("env_medium", invalid)["has_raw_value"])

    if env_broad_scale:
        obj["env_broad_scale_id"] = env_broad_scale.id
    if env_local_scale:
        obj["env_local_scale_id"] = env_local_scale.id
    if env_medium:
        obj["env_medium_id"] = env_medium.id

    project = omics_processing.find_one({"has_input": obj["id"]})
    if project is None:
        return
    obj["study_id"] = project["part_of"][0]
    if obj["study_id"] not in study_ids:
        return

    biosample = Biosample(**obj)
    db.add(models.Biosample(**biosample.dict()))


def load(db: Session, cursor: Cursor, omics_processing: Collection):
    for obj in cursor:
        try:
            load_biosample(db, obj, omics_processing)
        except Exception:
            logger.error("Error parsing biosample:")
            logger.error(json.dumps(obj, indent=2, default=str))
