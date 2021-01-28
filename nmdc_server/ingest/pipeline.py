import json
import logging
import re
from typing import Any, Dict, List, Tuple
from uuid import UUID, uuid4

from pymongo.collection import Collection
from pymongo.cursor import Cursor
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from typing_extensions import Protocol

from nmdc_server import models, schemas
from nmdc_server.crud import get_or_create

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
        }
    )
    if "function_limit" in kwargs:
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
load_mp_analysis = generate_pipeline_loader(
    schemas.MetaproteomicAnalysisBase, models.MetaproteomicAnalysis
)


def load(db: Session, cursor: Cursor, load_object: LoadObject, **kwargs):
    for obj in cursor:
        inputs = obj.pop("has_input", [])
        outputs = obj.pop("has_output", [])
        obj["project_id"] = obj.pop("was_informed_by")

        try:
            pipeline = load_object(db, obj, **kwargs)
        except Exception:
            logger.error(json.dumps(obj, indent=2, default=str))
            logger.exception("Error parsing pipeline")
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

        db.execute(
            models.DataObject.__table__.update()
            .where(models.DataObject.id.in_(inputs + outputs))
            .values({"project_id": pipeline.project_id})
        )
