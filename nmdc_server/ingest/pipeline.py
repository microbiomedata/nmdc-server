import logging
import re
from typing import Any, cast, Dict, List, Tuple
from uuid import UUID, uuid4

from pymongo.collection import Collection
from pymongo.cursor import Cursor
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from typing_extensions import Protocol

from nmdc_server import models, schemas
from nmdc_server.crud import get_or_create
from nmdc_server.ingest.errors import errors, missing as missing_

DataObjectList = List[str]
LoadObjectReturn = models.PipelineStep
ko_regex = re.compile(r"^KEGG\.ORTHOLOGY")
logger = logging.getLogger(__name__)


class LoadObject(Protocol):
    def __call__(self, db: Session, obj: Dict[str, Any], **kwargs: Any) -> LoadObjectReturn:
        ...


def load_mg_annotation(db: Session, obj: Dict[str, Any], **kwargs) -> LoadObjectReturn:
    pipeline = schemas.MetagenomeAnnotationBase(**obj)
    row = models.MetagenomeAnnotation(**pipeline.dict())
    db.add(row)
    db.flush()

    # TODO: fix populating gene functions
    annotations: Collection = kwargs["annotations"]

    query = annotations.find(
        {
            "was_generated_by": pipeline.id,
            "has_function": {
                "$regex": ko_regex,
            },
        },
        no_cursor_timeout=True,
    )
    if kwargs.get("function_limit"):
        query = query.limit(kwargs["function_limit"])

    gene_functions: Dict[str, models.GeneFunction] = {}
    mga_gene_functions: List[Tuple[UUID, str, str, str]] = []
    for gf in query:
        function_id = gf["has_function"]
        if function_id not in gene_functions:
            gene_functions[function_id] = get_or_create(
                db, models.GeneFunction, id=gf["has_function"]
            )[0]

        gene_function = gene_functions[function_id]
        db.add(gene_function)
        mga_gene_functions.append(
            (
                uuid4(),
                pipeline.id,
                function_id,
                gf["subject"],
            )
        )

    if mga_gene_functions:
        db.flush()
        db.execute(insert(models.MGAGeneFunction).values(mga_gene_functions))

    return row


def load_mags(db: Session, obj: Dict[str, Any], **kwargs) -> LoadObjectReturn:
    mags = obj.pop("mags_list", [])
    mags_analysis = load_mags_base(db, obj, **kwargs)
    for mag in mags:
        mag_dict = schemas.MAG(**mag).dict()
        mags_analysis.mags_list.append(models.MAG(**mag_dict))  # type: ignore

    return mags_analysis


def load_mp_analysis(db: Session, obj: Dict[str, Any], **kwargs) -> LoadObjectReturn:
    peptides = obj.pop("has_peptide_quantifications", [])
    pipeline = cast(models.MetaproteomicAnalysis, load_mp_analysis_base(db, obj, **kwargs))

    for p in peptides:
        if not db.query(models.MGAGeneFunction).filter_by(subject=p["best_protein"]).first():
            continue

        proteins = p.pop("all_proteins", [])
        peptide = models.MetaproteomicPeptide(metaproteomic_analysis=pipeline, **p)
        db.add(peptide)

        for protein in proteins:
            if not db.query(models.MGAGeneFunction).filter_by(subject=protein).first():
                continue
            db.add(
                models.PeptideMGAGeneFunction(
                    subject=protein,
                    metaproteomic_peptide=peptide,
                )
            )

    return pipeline


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


def load(db: Session, cursor: Cursor, load_object: LoadObject, workflow_type: str, **kwargs):
    remove_timezone_re = re.compile(r"Z\+\d+$", re.I)

    for obj in cursor:
        inputs = obj.pop("has_input", [])
        outputs = obj.pop("has_output", [])
        obj["omics_processing_id"] = obj.pop("was_informed_by")

        # TODO: pydantic should parse datetime like this... need to look into it
        #   2021-01-26T21:36:26.759770Z+0000
        if "started_at_time" in obj:
            obj["started_at_time"] = remove_timezone_re.sub("", obj["started_at_time"])
        if "ended_at_time" in obj:
            obj["ended_at_time"] = remove_timezone_re.sub("", obj["ended_at_time"])

        if db.query(models.OmicsProcessing).get(obj["omics_processing_id"]) is None:
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

        # TODO: Find a different way to validate ref. integrity
        valid_inputs = [d for d in inputs if db.query(models.DataObject).get(d)]
        valid_outputs = [d for d in outputs if db.query(models.DataObject).get(d)]

        missing_list = set(inputs + outputs) - set(valid_inputs + valid_outputs)
        for missing in missing_list:
            logger.warning(f"Unknown data object {missing}")
            missing_["data_object"].add(missing)

        inputs = valid_inputs
        outputs = valid_outputs

        for output in outputs:
            output.workflow_type = workflow_type
            db.add(output)

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

        db.execute(
            models.DataObject.__table__.update()
            .where(models.DataObject.id.in_(inputs + outputs))
            .values({"omics_processing_id": pipeline.omics_processing_id})
        )
