import json
import re
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import field_validator, model_validator
from pydantic.v1 import validator
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


omics_types = {
    "metagenome": "Metagenome",
    "metabolome": "Metabolomics",
    "metabolomics": "Metabolomics",
    "metaproteome": "Proteomics",
    "proteomics": "Proteomics",
    "metatranscriptome": "Metatranscriptome",
    "organic matter characterization": "Organic Matter Characterization",
    "nom": "Organic Matter Characterization",
}


class OmicsProcessing(OmicsProcessingCreate):
    _extract_value = validator("*", pre=True, allow_reuse=True)(extract_value)

    @model_validator(mode="before")
    def extract_extras(cls, values):
        return extract_extras(cls, values)

    @field_validator("add_date", "mod_date", mode="before")
    @classmethod
    def coerce_date(cls, v):
        if isinstance(v, str) and date_fmt.match(v):
            return datetime.strptime(v, "%d-%b-%y %I.%M.%S.%f000 %p").isoformat()
        return v


def is_biosample(object_id, biosample_collection):
    return list(biosample_collection.find({"id": object_id}))


def find_parent_process(output_id: str, mongodb: Database) -> Optional[dict[str, Any]]:
    """Given a ProcessedSample ID, find the process (e.g. Extraction) that created it."""
    material_processing_collection: Collection = mongodb["material_processing_set"]
    query = material_processing_collection.find({"has_output": output_id}, no_cursor_timeout=True)
    result_list = list(query)
    if len(result_list):
        return result_list[0]
    return None


def get_biosample_input_ids(input_id: str, mongodb: Database, results: set) -> set[Any]:
    """
    Given an input ID return all biosample objects that are included in the input resource.

    OmicsProcessing objects can take Biosamples or ProcessedSamples as inputs. Work needs to be done
    to determine which biosamples make up a given ProcessedSample. This function recursively tries
    to determine those Biosamples.
    """
    # Base case, the input is already a biosample
    biosample_collection: Collection = mongodb["biosample_set"]
    processed_sample_collection: Collection = mongodb["processed_sample_set"]
    if is_biosample(input_id, biosample_collection):
        results.add(input_id)
        return results

    # The given input is not a Biosample or Processed sample. Stop here.
    # Maybe this should report an error?
    query = list(processed_sample_collection.find({"id": input_id}, no_cursor_timeout=True))
    if not query:
        return results

    processed_sample_id = query[0]["id"]

    # Recursive case. For processed samples find the process that created it,
    # and check the inputs of that process.
    parent_process = find_parent_process(processed_sample_id, mongodb)
    if parent_process:
        for parent_input_id in parent_process["has_input"]:
            get_biosample_input_ids(parent_input_id, mongodb, results)
    return results


def load_omics_processing(db: Session, obj: Dict[str, Any], mongodb: Database, logger):
    logger = get_logger(__name__)
    input_ids: list[str] = obj.pop("has_input", [""])
    biosample_input_ids: set[str] = set()
    for input_id in input_ids:
        biosample_input_ids.union(get_biosample_input_ids(input_id, mongodb, biosample_input_ids))

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
    obj["study_id"] = obj.pop("associated_studies", [None])[0]
    obj["analyte_category"] = omics_types[obj["analyte_category"].lower()]
    obj["omics_type"] = omics_types[obj["analyte_category"].lower()]

    # Get instrument name
    instrument_id = obj.pop("instrument_used", [])
    if instrument_id:
        instrument = mongodb["instrument_set"].find_one({"id": instrument_id[0]})
        if instrument:
            obj["instrument_name"] = instrument["name"]

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
