import json
import re
from datetime import datetime
from typing import Any, Callable, Dict, Optional

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
    "lipidome": "Lipidomics",
    "lipidomics": "Lipidomics",
    "amplicon_sequencing_assay": "Amplicon",
    "amplicon": "Amplicon",
}


class OmicsProcessing(OmicsProcessingCreate):
    _extract_value = validator("*", pre=True, allow_reuse=True)(extract_value)

    @model_validator(mode="before")
    def extract_extras(cls, values):
        return extract_extras(cls, values)  # type: ignore

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


def get_biosample_input_ids(
    input_id: str,
    mongodb: Database,
    results: set[str],
    sampled_portions: set[str],
    direct_input: bool,
) -> set[Any]:
    """
    Given an input ID return all biosample objects that are included in the input resource.

    OmicsProcessing objects can take Biosamples or ProcessedSamples as inputs. Work needs to be done
    to determine which biosamples make up a given ProcessedSample. This function recursively tries
    to determine those Biosamples.

    As a side effect, a set of `sampled_portion` values gets populated. Whether or not a processed
    samples' `sampled_portion`s get added to the set is driven by the `direct_input` parameter. Only
    processed samples which are inputs directly to a data generation will have their
    `sampled_portion`s added.
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

    processed_sample = query[0]
    processed_sample_id = processed_sample["id"]
    sampled_portion = set(processed_sample.get("sampled_portion", []))
    # only store sampled portion values for immediate input to a data generation
    if direct_input and sampled_portion:
        sampled_portions.update(sampled_portion)

    # Recursive case. For processed samples find the process that created it,
    # and check the inputs of that process.
    parent_process = find_parent_process(processed_sample_id, mongodb)
    if parent_process:
        for parent_input_id in parent_process["has_input"]:
            get_biosample_input_ids(parent_input_id, mongodb, results, sampled_portions, False)
    return results


def get_configuration_property(
    mongodb: Database, configuration_id: str, key: str, config_map
) -> Optional[str]:
    config_set = "configuration_set"
    if configuration_id in config_map:
        config_record = config_map[configuration_id]
    else:
        config_record = mongodb[config_set].find_one({"id": configuration_id})
        config_map[configuration_id] = config_record
    return config_record[key] if config_record else None


def get_poolable_replicate_manifest(
    omics_processing_id: str,
    data_object_id: str,
    mongodb: Database,
) -> str:
    """
    Determine which poolable replicate manifest, if any, this data_generation is associated with.

    Returns either the ID of a manifest of type poolable_replicates, or the ID of the
    data_generation itself. Used for the purposes of counting data_generations for the Data Portal.
    """
    data_object_document = mongodb["data_object_set"].find_one({"id": data_object_id})
    if not data_object_document or not data_object_document.get("in_manifest", None):
        return omics_processing_id

    manifest_id = data_object_document.get("in_manifest")[0]
    manifest_document = mongodb["manifest_set"].find_one({"id": manifest_id})
    if manifest_document and manifest_document["manifest_category"] == "poolable_replicates":
        return manifest_id
    return omics_processing_id


def load_omics_processing(  # noqa: C901
    db: Session,
    obj: Dict[str, Any],
    mongodb: Database,
    logger,
    config_map,
):
    logger = get_logger(__name__)
    input_ids: list[str] = obj.pop("has_input", [""])
    biosample_input_ids: set[str] = set()
    sampled_portions: set[str] = set()
    for input_id in input_ids:
        biosample_input_ids.union(
            get_biosample_input_ids(input_id, mongodb, biosample_input_ids, sampled_portions, True)
        )
    if sampled_portions:
        obj["sampled_portions"] = list(sampled_portions)

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
    original_analyte_category = obj["analyte_category"].lower()
    obj["analyte_category"] = omics_types[original_analyte_category]
    obj["omics_type"] = omics_types[original_analyte_category]

    # Get amplicon specific fields
    if obj["omics_type"] == "Amplicon":

        def find_material_processing_having_id_in_output(id_: str) -> Optional[dict]:
            """
            Helper function that returns the first `material_processing_set` document, if any,
            whose `has_output` field contains the specified ID.
            """
            material_processing_set = mongodb["material_processing_set"]
            material_processing = material_processing_set.find_one({"has_output": id_})
            return material_processing

        load_amplicon_data(obj, input_ids, find_material_processing_having_id_in_output)

    # Get instrument name
    instrument_id = obj.pop("instrument_used", [])
    if instrument_id:
        instrument = mongodb["instrument_set"].find_one({"id": instrument_id[0]})
        if instrument:
            obj["instrument_name"] = instrument["name"]

    # Get configuration info
    mass_spec_config_id = obj.pop("has_mass_spectrometry_configuration", None)
    mass_spec_config_name = get_configuration_property(
        mongodb, mass_spec_config_id, "name", config_map
    )
    mass_spec_polarity_mode = get_configuration_property(
        mongodb, mass_spec_config_id, "polarity_mode", config_map
    )
    if mass_spec_config_name:
        obj["mass_spectrometry_configuration_name"] = mass_spec_config_name
        obj["mass_spectrometry_configuration_id"] = mass_spec_config_id
        obj["mass_spectrometry_config_polarity_mode"] = mass_spec_polarity_mode

    chromatography_config_id = obj.pop("has_chromatography_configuration", None)
    chromatography_config_name = get_configuration_property(
        mongodb, chromatography_config_id, "name", config_map
    )
    if chromatography_config_name:
        obj["chromatography_configuration_name"] = chromatography_config_name
        obj["chromatography_configuration_id"] = chromatography_config_id

    omics_processing = models.OmicsProcessing(**OmicsProcessing(**obj).dict())
    for biosample_object in biosample_input_objects:
        # mypy thinks that omics_processing.biosample_inputs is of type Biosample
        omics_processing.biosample_inputs.append(biosample_object)

    manifest_id: str = omics_processing.id
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
        omics_processing.outputs.append(data_object)

        manifest_id = get_poolable_replicate_manifest(omics_processing.id, data_object_id, mongodb)

    omics_processing.poolable_replicates_manifest_id = manifest_id
    db.add(omics_processing)


def load_amplicon_data(
    obj,
    input_ids,
    find_material_processing_having_id_in_output: Callable[[str], Optional[dict]],
):
    """
    Load amplicon-specific fields onto a data generation record.

    Here, "data generation" is the modern NMDC term for what the surrounding ingest code
    still calls an "omics processing" record; they refer to the same thing.

    ``target_gene`` and ``target_subfragment`` are optional, independent slots on
    ``LibraryPreparation``: either, both, or neither may be present. Each is read
    independently from the first LibraryPreparation in this data generation's input chain
    that declares it, so a ``target_subfragment`` is captured even when its source
    LibraryPreparation omits ``target_gene`` (and vice versa). All inputs are scanned, so a
    value on any of them is picked up.

    Following the convention of load_omics_processing, this mutates `obj` in place rather
    than returning a value.

    Args:
        obj: The data generation record to populate with amplicon data (mutated in place)
        input_ids: List of input IDs to search for the producing LibraryPreparation
        find_material_processing_having_id_in_output: A callback function that returns the first
                                                      `material_processing_set` document, if any,
                                                      whose `has_output` field contains the
                                                      specified ID.

    Doctests (these can be run via `$ python -m doctest nmdc_server/ingest/omics_processing.py`):

    1. Neither ``target_gene`` nor ``target_subfragment`` present:
    >>> obj = {}
    >>> load_amplicon_data(obj, ["input_a"], lambda id_: {"id": "nmdc:libprep-1"})
    >>> obj
    {'target_gene': None, 'target_subfragment': None}

    2. Only ``target_subfragment`` present:
    >>> obj = {}
    >>> load_amplicon_data(obj, ["input_a"], lambda id_: {"target_subfragment": {"has_raw_value": "MySubfragment"}})
    >>> obj
    {'target_gene': None, 'target_subfragment': 'MySubfragment'}

    3. Only ``target_gene`` present:
    >>> obj = {}
    >>> load_amplicon_data(obj, ["input_a"], lambda id_: {"target_gene": "MyGene"})
    >>> obj
    {'target_gene': 'MyGene', 'target_subfragment': None}

    4. Both ``target_gene`` and ``target_subfragment`` present:
    >>> obj = {}
    >>> load_amplicon_data(obj, ["input_a"], lambda id_: {"target_gene": "MyGene", "target_subfragment": {"has_raw_value": "MySubfragment"}})
    >>> obj
    {'target_gene': 'MyGene', 'target_subfragment': 'MySubfragment'}

    5. No LibraryPreparation is found for any input (callback returns None):
    >>> obj = {}
    >>> load_amplicon_data(obj, ["input_a"], lambda id_: None)
    >>> obj
    {'target_gene': None, 'target_subfragment': None}

    6. No input IDs at all:
    >>> obj = {}
    >>> load_amplicon_data(obj, [], lambda id_: None)
    >>> obj
    {'target_gene': None, 'target_subfragment': None}

    7. Multiple inputs whose LibraryPreparations each carry only one field; both are collected:
    >>> obj = {}
    >>> lib_preps = {"input_a": {"target_gene": "MyGene"}, "input_b": {"target_subfragment": {"has_raw_value": "MySubfragment"}}}
    >>> load_amplicon_data(obj, ["input_a", "input_b"], lib_preps.get)
    >>> obj
    {'target_gene': 'MyGene', 'target_subfragment': 'MySubfragment'}
    """
    obj["target_gene"] = None
    obj["target_subfragment"] = None

    for input_id in input_ids:
        # `obj` is the destination data generation record being populated; `amplicon_lib_prep`
        # is a source LibraryPreparation the target_gene/target_subfragment are read from.
        amplicon_lib_prep = find_material_processing_having_id_in_output(input_id)
        if not amplicon_lib_prep:
            continue

        # target_gene and target_subfragment are independent optional slots, so capture each
        # separately the first time an input's LibraryPreparation declares it.
        if obj["target_gene"] is None:
            obj["target_gene"] = amplicon_lib_prep.get("target_gene")

        if obj["target_subfragment"] is None:
            # target_subfragment's schema range is TextValue, so a present value is a
            # `{"has_raw_value": ...}` dict; store its raw value (absent -> left as None).
            target_subfragment = amplicon_lib_prep.get("target_subfragment")
            if isinstance(target_subfragment, dict):
                obj["target_subfragment"] = target_subfragment.get("has_raw_value")


def load(db: Session, cursor: Cursor, mongodb: Database):
    logger = get_logger(__name__)
    config_map: dict[str, dict[str, Any]] = {}
    for obj in cursor:
        try:
            load_omics_processing(db, obj, mongodb, logger, config_map)
        except Exception as err:
            logger.error(err)
            logger.error("Error parsing omics_processing:")
            logger.error(json.dumps(obj, indent=2, default=str))
            errors["omics_processing"].add(obj["id"])
    db.commit()
