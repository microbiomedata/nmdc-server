import json
import re
from datetime import datetime
from typing import Any, Dict

from pydantic import root_validator, validator
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
            if "latitude" in values["lat_lon"] and "longitude" in values["lat_lon"]:
                values["latitude"] = values["lat_lon"]["latitude"]
                values["longitude"] = values["lat_lon"]["longitude"]
            else:
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

    @validator("collection_date", pre=True)
    def coerce_collection_date(cls, value):
        # { "has_raw_value": ... }
        raw_value = value["has_raw_value"]
        expected_formats = [
            "%d-%b-%y %I.%M.%S.%f000 %p",
            "%y-%m-%dT%I:%M:%S",
            "%y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%I:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S%z",
            "%y-%m-%d %I:%M:%S",
            "%y-%m-%d %H:%M:%S",
            "%Y-%m-%d %I:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%dT%H:%MZ",
        ]
        for date_format in expected_formats:
            try:
                dt = datetime.strptime(raw_value, date_format).isoformat()
                return dt
            except ValueError:
                continue
        if isinstance(raw_value, str) and date_fmt.match(raw_value):
            return datetime.strptime(raw_value, "%d-%b-%y %I.%M.%S.%f000 %p").isoformat()
        try:
            dt = datetime.strptime(raw_value, "%Y-%m-%d").isoformat()
            return dt
        except ValueError:
            try:
                raw_value = raw_value + "-01"
                dt = datetime.strptime(raw_value, "%Y-%m-%d").isoformat()
                return dt
            except ValueError:
                try:
                    raw_value = raw_value + "-01"
                    dt = datetime.strptime(raw_value, "%Y-%m-%d").isoformat()
                    return dt
                except ValueError:
                    # The raw value may be parseable by pydantic.
                    # If not, we will a validation error in the
                    # ingest output
                    return raw_value


def load_biosample(db: Session, obj: Dict[str, Any]):
    logger = get_logger(__name__)
    env_broad_scale_id = obj.pop("env_broad_scale", {}).get("term", {}).get("id", "")
    env_broad_scale = db.query(models.EnvoTerm).get(env_broad_scale_id.replace("_", ":"))
    env_local_scale_id = obj.pop("env_local_scale", {}).get("term", {}).get("id", "")
    env_local_scale = db.query(models.EnvoTerm).get(env_local_scale_id.replace("_", ":"))
    env_medium_id = obj.pop("env_medium", {}).get("term", {}).get("id", "")
    env_medium = db.query(models.EnvoTerm).get(env_medium_id.replace("_", ":"))

    if env_broad_scale:
        obj["env_broad_scale_id"] = env_broad_scale.id
    if env_local_scale:
        obj["env_local_scale_id"] = env_local_scale.id
    if env_medium:
        obj["env_medium_id"] = env_medium.id

    part_of = obj.pop("associated_studies", None)
    if part_of is None:
        logger.error(f"Could not determine study for biosample {obj['id']}")
        return

    obj["study_id"] = part_of[0]
    depth_obj = obj.get("depth", {})
    obj["depth"] = extract_quantity(depth_obj, "biosample", "depth")

    biosample = Biosample(**obj)

    # Merge other ambiguously named alternate identifier columns
    # TODO remove the hack to filter out gold from the alternate IDs
    biosample.alternate_identifiers += filter(
        lambda x: not x.lower().startswith("gold:"),
        obj.get("alternative_identifiers", []),
    )
    biosample.alternate_identifiers += obj.get("insdc_biosample_identifiers", [])
    biosample.alternate_identifiers += obj.get("insdc_secondary_sample_identifiers", [])
    biosample.alternate_identifiers += obj.get("gold_biosample_identifiers", [])
    biosample.alternate_identifiers += obj.get("igsn_biosample_identifiers", [])
    biosample.alternate_identifiers += obj.get("img_identifiers", [])

    biosample.emsl_biosample_identifiers = obj.get("emsl_biosample_identifiers", [])

    # Store entire depth object, which may represent a range
    if biosample.annotations is not None:
        biosample.annotations["depth"] = depth_obj

    db.add(models.Biosample(**biosample.dict()))


def load(db: Session, cursor: Cursor):
    logger = get_logger(__name__)
    for obj in cursor:
        try:
            load_biosample(db, obj)
        except Exception as err:
            logger.error(f"Error parsing biosample: {err}")
            logger.error(json.dumps(obj, indent=2, default=str))
            errors["biosample"].add(obj["id"])
