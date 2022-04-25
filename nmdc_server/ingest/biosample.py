import json
import re
from datetime import datetime
from typing import Any, Dict

from pydantic import root_validator, validator
from pymongo.collection import Collection
from pymongo.cursor import Cursor
from sqlalchemy.orm import Session

from nmdc_server import models
from nmdc_server.attribute_units import extract_quantity
from nmdc_server.ingest.common import extract_extras, extract_value
from nmdc_server.ingest.errors import errors
from nmdc_server.logger import get_logger
from nmdc_server.schemas import BiosampleCreate

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
        return v


def load_biosample(db: Session, obj: Dict[str, Any], omics_processing: Collection):
    logger = get_logger(__name__)
    invalid = {"has_raw_value": ""}
    env_broad_scale = db.query(models.EnvoTerm).get(
        obj.pop("env_broad_scale", invalid)["has_raw_value"].replace("_", ":")
    )
    env_local_scale = db.query(models.EnvoTerm).get(
        obj.pop("env_local_scale", invalid)["has_raw_value"].replace("_", ":")
    )
    env_medium = db.query(models.EnvoTerm).get(
        obj.pop("env_medium", invalid)["has_raw_value"].replace("_", ":")
    )

    if env_broad_scale:
        obj["env_broad_scale_id"] = env_broad_scale.id
    if env_local_scale:
        obj["env_local_scale_id"] = env_local_scale.id
    if env_medium:
        obj["env_medium_id"] = env_medium.id

    omics_processing_record = omics_processing.find_one({"has_input": obj["id"]})
    part_of = obj.pop("part_of", None)
    if part_of is None:
        if omics_processing_record is None:
            logger.error(f"Could not determine study for biosample {obj['id']}")
            return
        part_of = omics_processing_record["part_of"]

    obj["study_id"] = part_of[0]
    obj["depth"] = extract_quantity(obj.get("depth", {}), "biosample", "depth")
    if obj["depth"] is None:
        obj["depth"] = extract_quantity(obj.pop("depth2", {}), "biosample", "depth")

    biosample = Biosample(**obj)

    # Merge other ambiguously named alternate identifier columns
    # TODO remove the hack to filter out gold from the alternate IDs
    biosample.alternate_identifiers += filter(
        lambda x: not x.lower().startswith("gold:"),
        obj.get("alternative_identifiers", []),
    )
    biosample.alternate_identifiers += obj.get("INSDC_biosample_identifiers", [])
    biosample.alternate_identifiers += obj.get("GOLD_sample_identifiers", [])

    db.add(models.Biosample(**biosample.dict()))


def load(db: Session, cursor: Cursor, omics_processing: Collection):
    logger = get_logger(__name__)
    for obj in cursor:
        try:
            load_biosample(db, obj, omics_processing)
        except Exception as err:
            logger.error(f"Error parsing biosample: {err}")
            logger.error(json.dumps(obj, indent=2, default=str))
            errors["biosample"].add(obj["id"])
