import re
from typing import Any, Dict, Iterable, List, Set, cast

from pymongo.collection import Collection
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from typing_extensions import Protocol

from nmdc_server import models, schemas
from nmdc_server.ingest.errors import errors
from nmdc_server.ingest.errors import missing as missing_
from nmdc_server.logger import get_logger

DataObjectList = List[str]
LoadObjectReturn = models.PipelineStep
gene_regex = re.compile(r"^(KEGG\.ORTHOLOGY|COG|PFAM)")


class LoadObject(Protocol):
    def __call__(self, db: Session, obj: Dict[str, Any], **kwargs: Any) -> LoadObjectReturn: ...


# Load metagenome annotation as well as the gene function annotations produced.
def load_mg_annotation(db: Session, obj: Dict[str, Any], **kwargs) -> LoadObjectReturn:
    pipeline = schemas.MetagenomeAnnotationBase(**obj)
    row = models.MetagenomeAnnotation(**pipeline.dict())
    db.add(row)
    db.flush()

    annotations: Collection = kwargs["annotations"]

    query = annotations.find(
        {
            "was_generated_by": pipeline.id,
            "gene_function_id": {
                "$regex": gene_regex,
            },
        },
        no_cursor_timeout=True,
        projection={
            "_id": False,
            "was_generated_by": True,
            "count": True,
            "gene_function_id": True,
        },
    )
    if kwargs.get("function_limit"):
        query = query.limit(kwargs["function_limit"])

    gene_functions: Set[str] = set()
    mga_gene_function_aggregations: List[models.MGAGeneFunctionAggregation] = []
    for annotation in query:
        function_id = annotation["gene_function_id"]
        gene_functions.add(function_id)
        mga_gene_function_aggregations.append(
            models.MGAGeneFunctionAggregation(
                metagenome_annotation_id=pipeline.id,
                gene_function_id=function_id,
                count=annotation["count"],
            )
        )

    if mga_gene_function_aggregations:
        db.execute(
            insert(models.GeneFunction)
            .on_conflict_do_nothing()
            .values([(gf,) for gf in gene_functions])
        )
        db.bulk_save_objects(mga_gene_function_aggregations)

    return row


def load_mags(db: Session, obj: Dict[str, Any], **kwargs) -> LoadObjectReturn:
    mags = obj.pop("mags_list", [])
    mags_analysis = load_mags_base(db, obj, **kwargs)
    for mag in mags:
        mag_dict = schemas.MAG(**mag).dict()
        mags_analysis.mags_list.append(models.MAG(**mag_dict))  # type: ignore

    return mags_analysis


def load_mp_analysis(db: Session, obj: Dict[str, Any], **kwargs) -> LoadObjectReturn:
    pipeline = cast(models.MetaproteomicAnalysis, load_mp_analysis_base(db, obj, **kwargs))

    annotations: Collection = kwargs["annotations"]

    query = annotations.find(
        {
            "was_generated_by": pipeline.id,
            "gene_function_id": {
                "$regex": gene_regex,
            },
        },
        no_cursor_timeout=True,
        projection={
            "_id": False,
            "was_generated_by": True,
            "count": True,
            "gene_function_id": True,
        },
    )
    if kwargs.get("function_limit"):
        query = query.limit(kwargs["function_limit"])

    gene_functions: Set[str] = set()
    metap_gene_function_aggregations: List[models.MetaPGeneFunctionAggregation] = []
    for annotation in query:
        function_id = annotation["gene_function_id"]
        gene_functions.add(function_id)
        metap_gene_function_aggregations.append(
            models.MetaPGeneFunctionAggregation(
                metaproteomic_analysis_id=pipeline.id,
                gene_function_id=function_id,
                count=annotation["count"],
            )
        )
    if metap_gene_function_aggregations:
        db.execute(
            insert(models.GeneFunction)
            .on_conflict_do_nothing()
            .values([(gf,) for gf in gene_functions])
        )
        db.bulk_save_objects(metap_gene_function_aggregations)

    return pipeline


def load_mt_annotation(db: Session, obj: Dict[str, Any], **kwargs) -> LoadObjectReturn:
    # Ingest the MetatranscriptomeAnnotation record
    pipeline = cast(models.MetatranscriptomeAnnotation, load_mt_annotation_base(db, obj, **kwargs))

    annotations: Collection = kwargs["annotations"]

    # Query gene function annotations from mongo and build the appropriate objects
    query = annotations.find(
        {
            "was_generated_by": pipeline.id,
            "gene_function_id": {
                "$regex": gene_regex,
            },
        },
        no_cursor_timeout=True,
        projection={
            "_id": False,
            "was_generated_by": True,
            "count": True,
            "gene_function_id": True,
        },
    )
    if kwargs.get("function_limit"):
        query = query.limit(kwargs["function_limit"])

    gene_functions: Set[str] = set()
    gene_function_aggregations: List[models.MetaTGeneFunctionAggregation] = []
    for annotation in query:
        function_id = annotation["gene_function_id"]
        gene_functions.add(function_id)
        gene_function_aggregations.append(
            models.MetaTGeneFunctionAggregation(
                metatranscriptome_annotation_id=pipeline.id,
                gene_function_id=function_id,
                count=annotation["count"],
            )
        )
    # Save both newly encountered gene functions and the gene function aggregations
    if gene_function_aggregations:
        db.execute(
            insert(models.GeneFunction)
            .on_conflict_do_nothing()
            .values([(gf,) for gf in gene_functions])
        )
        db.bulk_save_objects(gene_function_aggregations)

    return pipeline


# This is a loader for a generic workflow type that doesn't need any
# additional processing.
def generate_pipeline_loader(schema, model) -> LoadObject:
    def loader(db: Session, obj: Dict[str, Any], **kwargs: Any) -> LoadObjectReturn:
        pipeline_dict = schema(**obj)
        pipeline = model(**pipeline_dict.dict())
        db.add(pipeline)
        db.flush()
        return pipeline

    return loader


load_reads_qc = generate_pipeline_loader(schemas.ReadsQCBase, models.ReadsQC)
load_mg_assembly = generate_pipeline_loader(
    schemas.MetagenomeAssemblyBase, models.MetagenomeAssembly
)
load_mp_analysis_base = generate_pipeline_loader(
    schemas.MetaproteomicAnalysisBase, models.MetaproteomicAnalysis
)
load_mags_base = generate_pipeline_loader(schemas.MAGsAnalysisBase, models.MAGsAnalysis)
load_nom_analysis = generate_pipeline_loader(schemas.NOMAnalysisBase, models.NOMAnalysis)
load_read_based_analysis = generate_pipeline_loader(
    schemas.ReadBasedAnalysisBase, models.ReadBasedAnalysis
)
load_metabolomics_analysis = generate_pipeline_loader(
    schemas.MetabolomicsAnalysisBase, models.MetabolomicsAnalysis
)
load_metatranscriptome = generate_pipeline_loader(
    schemas.MetatranscriptomeBase, models.Metatranscriptome
)
load_mt_assembly = generate_pipeline_loader(
    schemas.MetatranscriptomeAssemblyBase, models.MetatranscriptomeAssembly
)
load_mt_annotation_base = generate_pipeline_loader(
    schemas.MetatranscriptomeAnnotationBase, models.MetatranscriptomeAnnotation
)


# This is a generic function for load workflow execution objects.  Some workflow types require
# custom processing arguments that get passed in as kwargs.
# flake8: noqa: C901
def load(
    db: Session,
    cursor: Iterable[Dict[str, Any]],
    load_object: LoadObject,
    workflow_type: str,
    **kwargs,
):
    logger = get_logger(__name__)
    remove_timezone_re = re.compile(r"Z\+\d+$", re.I)

    for obj in cursor:
        inputs = obj.pop("has_input", [])
        outputs = obj.pop("has_output", [])

        if workflow_type is not None:
            # unset the type, override it with the schema's default type
            reported_type = obj.pop("type")
            if reported_type != workflow_type:
                logger.warning(f"Unexpected type {reported_type} (expected {workflow_type})")

        was_informed_by: str | list[str] = obj.pop("was_informed_by")
        if isinstance(was_informed_by, str):
            was_informed_by = [was_informed_by]
        obj["omics_processing_id"] = was_informed_by[0]
        obj["was_informed_by"] = was_informed_by

        # TODO: pydantic should parse datetime like this... need to look into it
        #   2021-01-26T21:36:26.759770Z+0000
        if "started_at_time" in obj:
            obj["started_at_time"] = remove_timezone_re.sub("", obj["started_at_time"])
        if "ended_at_time" in obj:
            obj["ended_at_time"] = remove_timezone_re.sub("", obj["ended_at_time"])

        if db.query(models.OmicsProcessing).get(obj["omics_processing_id"]) is None:
            logger.error(
                f"Encountered pipeline with no associated omics_processing: {obj['omics_processing_id']}"
            )
            continue

        try:
            pipeline = load_object(db, obj, **kwargs)
            db.commit()
        except Exception:
            logger.exception(f"Error parsing pipeline {obj['id']}")
            errors["pipeline"].add(obj["id"])
            db.rollback()
            continue

        id_ = pipeline.id
        table_name = pipeline.__tablename__

        input_association = getattr(models, f"{table_name}_input_association")
        output_association = getattr(models, f"{table_name}_output_association")
        was_informed_by_association = getattr(models, f"{table_name}_data_generation_association")

        # TODO: Find a different way to validate ref. integrity
        valid_inputs = [d for d in inputs if db.query(models.DataObject).get(d)]
        valid_outputs = [d for d in outputs if db.query(models.DataObject).get(d)]

        # historically a lot of data objects listed in the workflow entities do
        # not exist in the data_object collection... these are collected and
        # reported at the end of the run
        missing_list = set(inputs + outputs) - set(valid_inputs + valid_outputs)
        for missing in missing_list:
            logger.warning(f"Unknown data object {missing} for {obj['id']}")
            missing_["data_object"].add(missing)

        inputs = valid_inputs
        outputs = valid_outputs

        db.flush()
        if inputs:
            db.execute(
                insert(input_association)
                .values([(id_, f) for f in inputs])
                .on_conflict_do_nothing()
            )
        if outputs:
            db.execute(
                insert(output_association)
                .values([(id_, f) for f in outputs])
                .on_conflict_do_nothing()
            )
        if was_informed_by:
            db.execute(
                insert(was_informed_by_association)
                .values([(id_, data_generation) for data_generation in was_informed_by])
                .on_conflict_do_nothing()
            )

            for data_generation in was_informed_by:
                data_objects = inputs + outputs
                db.execute(
                    insert(models.omics_processing_output_association)
                    .values([(data_generation, data_object) for data_object in data_objects])
                    .on_conflict_do_nothing()
                )

        for id_ in outputs:
            output = db.query(models.DataObject).get(id_)
            assert output
            output.workflow_type = workflow_type
            db.add(output)
