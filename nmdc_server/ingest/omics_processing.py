import json
import re
from datetime import datetime
from typing import Any, Dict

from pydantic import root_validator, validator
from pymongo.cursor import Cursor
from sqlalchemy.orm import Session

from nmdc_server import models
from nmdc_server.data_object_filters import WorkflowActivityTypeEnum
from nmdc_server.ingest.common import extract_extras, extract_value
from nmdc_server.ingest.errors import errors
from nmdc_server.ingest.errors import missing as missing_
from nmdc_server.logger import get_logger
from nmdc_server.schemas import OmicsProcessingCreate

date_fmt = re.compile(r"\d\d-[A-Z]+-\d\d \d\d\.\d\d\.\d\d\.\d+ [AP]M")


class OmicsProcessing(OmicsProcessingCreate):
    _extract_value = validator("*", pre=True, allow_reuse=True)(extract_value)

    @root_validator(pre=True)
    def extract_extras(cls, values):
        return extract_extras(cls, values)

    @validator("add_date", "mod_date", pre=True)
    def coerce_date(cls, v):
        if isinstance(v, str) and date_fmt.match(v):
            return datetime.strptime(v, "%d-%b-%y %I.%M.%S.%f000 %p").isoformat()
        return v


def load_omics_processing(db: Session, obj: Dict[str, Any]):
    logger = get_logger(__name__)
    obj["biosample_id"] = obj.pop("has_input", [None])[0]
    data_objects = obj.pop("has_output", [])
    obj["study_id"] = obj.pop("part_of", [None])[0]

    if obj["biosample_id"] and db.query(models.Biosample).get(obj["biosample_id"]) is None:
        logger.warn(f"Unknown biosample {obj['biosample_id']}")
        missing_["biosample"].add(obj.pop("biosample_id"))

    omics_processing = models.OmicsProcessing(**OmicsProcessing(**obj).dict())

    for data_object_id in data_objects:
        data_object = db.query(models.DataObject).get(data_object_id)
        if data_object is None:
            logger.warning(f"Unknown data object {data_object_id}")
            missing_["data_object"].add(data_object_id)
            continue

        data_object.omics_processing = omics_processing

        # add a custom workflow type for raw data (data that is the direct
        # output of an omics_processing)
        data_object.workflow_type = WorkflowActivityTypeEnum.raw_data.value
        db.add(data_object)
        omics_processing.outputs.append(data_object)  # type: ignore

    db.add(omics_processing)


def load(db: Session, cursor: Cursor):
    logger = get_logger(__name__)
    for obj in cursor:
        try:
            load_omics_processing(db, obj)
        except Exception:
            logger.error("Error parsing omics_processing:")
            logger.error(json.dumps(obj, indent=2, default=str))
            errors["omics_processing"].add(obj["id"])
    db.commit()
