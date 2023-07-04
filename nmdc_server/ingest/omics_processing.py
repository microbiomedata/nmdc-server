import json
import re
from datetime import datetime
from typing import Any, Dict

from pydantic import root_validator, validator
from pymongo.collection import Collection
from pymongo.cursor import Cursor
from pymongo.database import Database
from sqlalchemy.orm import Session

from nmdc_server import models
from nmdc_server.data_object_filters import WorkflowActivityTypeEnum
from nmdc_server.ingest.common import extract_extras, extract_value
from nmdc_server.ingest.errors import errors
from nmdc_server.ingest.errors import missing as missing_
from nmdc_server.logger import get_logger
from nmdc_server.schemas import OmicsProcessingCreate

date_fmt = re.compile(r"\d\d-[A-Z]+-\d\d \d\d\.\d\d\.\d\d\.\d+ [AP]M")

input_types = {
    "biosample",
    "processed_sample",
}

process_types = {
    # "processed_sample",
    "pooling",
    "extraction" "library_preperation",
}


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


omics_types = {
    "metagenome": "Metagenome",
    "metabolomics": "Metabolomics",
    "proteomics": "Proteomics",
    "metatranscriptome": "Metatranscriptome",
    "organic matter characterization": "Organic Matter Characterization",
}


collections = {
    "biosample": "biosample_set",
    "processed_sample": "processed_sample_set",
    "extraction": "extraction_set",
    "library_preparation": "library_preparation_set",
    "pooling": "pooling",
}


def is_biosample(id, biosample_collection):
    return list(biosample_collection.find({"id": id}))


def find_parent_process(output_id, mongodb):
    output_found = False
    collections_left = True
    while not output_found and collections_left:
        for name in process_types:
            collection: Collection = mongodb[collections[name]]
            query = list(collection.find({"has_output": output_id}, no_cursor_timeout=True))
            if len(query):
                output_found = True
                return query[0]
        collections_left = False
    return None


def get_biosample_input_ids(input_id, mongodb, logger, results=[]) -> list[Any]:
    # Check if the input is a biosample
    biosample_collection: Collection = mongodb["biosample_set"]
    processed_sample_collection: Collection = mongodb["processed_sample_set"]
    if is_biosample(input_id, biosample_collection):
        results += [input_id]
        return results

    logger.error("non-biosample input")

    query = list(processed_sample_collection.find({"id": input_id}, no_cursor_timeout=True))
    if not query:
        # throw error?
        return results

    processed_sample_id = query[0]["id"]

    # For processed samples find the process that created it
    parent_process = find_parent_process(processed_sample_id, mongodb)
    if parent_process:
        # we have an extraction, library preparation, or pooling
        # assume all inputs for pooling are biosamples
        for input_id in parent_process["has_input"]:
            get_biosample_input_ids(input_id, mongodb, results)
    return results


def load_omics_processing(db: Session, obj: Dict[str, Any], mongodb: Database, logger):
    logger = get_logger(__name__)
    input_ids = obj.pop("has_input", [None])
    biosample_input_ids = []
    for input_id in input_ids:
        biosample_input_ids += get_biosample_input_ids(input_id, mongodb, logger)
    if len(biosample_input_ids) > 1:
        logger.error("Processed sample input detected")
        logger.error(obj["id"])
        logger.error(biosample_input_ids)

    obj["biosample_inputs"] = []
    biosample_input_objects = []
    for biosample_id in biosample_input_ids:
        biosample_object = db.query(models.Biosample).get(biosample_id)
        if not biosample_object:
            logger.warn(f"Unknown biosample {biosample_id}")
            missing_["biosample"].add(biosample_id)
        else:
            biosample_input_objects.append(biosample_object)

    data_objects = obj.pop("has_output", [])
    obj["study_id"] = obj.pop("part_of", [None])[0]
    raw_omics_type: str = obj["omics_type"]["has_raw_value"]
    obj["omics_type"]["has_raw_value"] = omics_types[raw_omics_type.lower()]

    omics_processing = models.OmicsProcessing(**OmicsProcessing(**obj).dict())
    for biosample_object in biosample_input_objects:
        # mypy thinks that omics_processing.biosample_inputs is of type Biosample
        omics_processing.biosample_inputs.append(biosample_object)  # type: ignore

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


def load(db: Session, cursor: Cursor, mongodb: Database):
    logger = get_logger(__name__)
    for obj in cursor:
        try:
            load_omics_processing(db, obj, mongodb, logger)
        except Exception as err:
            logger.error(err)
            logger.error("Error parsing omics_processing:")
            logger.error(json.dumps(obj, indent=2, default=str))
            errors["omics_processing"].add(obj["id"])
    db.commit()
