from typing import Any, Dict, Iterator

import click
from pymongo import MongoClient
from pymongo.collection import Collection
from sqlalchemy.orm import Session

from nmdc_server import models
from nmdc_server.config import Settings
from nmdc_server.data_object_filters import WorkflowActivityTypeEnum
from nmdc_server.ingest import (
    biosample,
    data_object,
    envo,
    kegg,
    omics_processing,
    pipeline,
    search_index,
    study,
)
from nmdc_server.logger import get_logger


# Custom mongo cursor pagination.  This exists because some of the
# queries timeout before all the results can be processed.
def paginate_cursor(
    collection: Collection, page_size: int = 100, **kwargs
) -> Iterator[Dict[str, Any]]:
    skip = 0
    last_iteration_count = page_size
    while last_iteration_count == page_size:
        cursor = collection.find(**kwargs).limit(page_size).skip(skip)
        last_iteration_count = 0
        for obj in cursor:
            last_iteration_count += 1
            yield obj
        skip = skip + page_size


def load(db: Session, function_limit=None, skip_annotation=False):
    """Ingest all data from the mongodb source.

    Optionally, you can limit the number of gene functions per omics_processing
    to allow for a faster ingest for testing.  The full result set takes several
    hours to process.

    This function is called both from the CLI (for development) and from the ingest
    celery function (in production).  Watch for warnings during ingest for ignored
    entities due to invalid foreign key references.
    """
    logger = get_logger(__name__)
    settings = Settings()
    if not (settings.mongo_user and settings.mongo_password):
        raise Exception("Please set NMDC_MONGO_USER and NMDC_MONGO_PASSWORD")

    client: MongoClient = MongoClient(
        host=settings.mongo_host,
        username=settings.mongo_user,
        password=settings.mongo_password,
        port=settings.mongo_port,
        directConnection=True,
    )
    mongodb = client[settings.mongo_database]

    logger.info("Loading envo terms...")
    envo.load(db)
    db.commit()

    logger.info("Loading Kegg orthology...")
    kegg.load(db)
    db.commit()

    logger.info("Loading studies...")
    study.load(db, mongodb["study_set"].find())
    db.commit()

    logger.info("Loading data objects...")
    data_object.load(
        db,
        mongodb["data_object_set"].find(),
        list(mongodb["file_type_enum"].find()),
    )
    db.commit()

    # Only grab biosamples associated with studies we are ingesting.
    logger.info("Loading biosamples...")
    cursor = mongodb["biosample_set"].find(
        no_cursor_timeout=True,
    )
    biosample.load(
        db,
        cursor,
    )
    db.commit()

    logger.info("Loading omics processing...")
    omics_processing.load(
        db,
        mongodb["data_generation_set"].find(),
        mongodb,
    )
    db.commit()

    workflow_set = "workflow_execution_set"

    logger.info("Loading metabolomics analysis...")
    pipeline.load(
        db,
        mongodb[workflow_set].find({"type": WorkflowActivityTypeEnum.metabolomics_analysis.value}),
        pipeline.load_metabolomics_analysis,
        WorkflowActivityTypeEnum.metabolomics_analysis.value,
    )
    db.commit()

    logger.info("Loading read based analysis...")
    pipeline.load(
        db,
        mongodb[workflow_set].find({"type": WorkflowActivityTypeEnum.read_based_analysis.value}),
        pipeline.load_read_based_analysis,
        WorkflowActivityTypeEnum.read_based_analysis.value,
    )
    db.commit()

    logger.info("Loading metatranscriptome expression analyses...")
    pipeline.load(
        db,
        mongodb[workflow_set].find(
            {"type": WorkflowActivityTypeEnum.metatranscriptome_expression.value}
        ),
        pipeline.load_metatranscriptome,
        WorkflowActivityTypeEnum.metatranscriptome_expression.value,
    )

    logger.info("Loading metatranscriptome assemblies...")
    pipeline.load(
        db,
        mongodb[workflow_set].find(
            {"type": WorkflowActivityTypeEnum.metatranscriptome_assembly.value}
        ),
        pipeline.load_mt_assembly,
        WorkflowActivityTypeEnum.metatranscriptome_assembly.value,
    )

    logger.info("Loading NOM analysis...")
    pipeline.load(
        db,
        mongodb[workflow_set].find({"type": WorkflowActivityTypeEnum.nom_analysis.value}),
        pipeline.load_nom_analysis,
        WorkflowActivityTypeEnum.nom_analysis.value,
    )
    db.commit()

    logger.info("Loading MAGs...")
    pipeline.load(
        db,
        mongodb[workflow_set].find({"type": WorkflowActivityTypeEnum.mags_analysis.value}),
        pipeline.load_mags,
        WorkflowActivityTypeEnum.mags_analysis.value,
    )
    db.commit()

    if skip_annotation is False:
        try:
            # This section has its own subprogress bar because it takes several
            # hours to ingest all of the gene function products from the metag
            # workflows.
            logger.info("Loading metagenome annotation...")

            # This has historically been fast, but it is only for the progress bar.
            # It can be removed if it becomes slow.
            annotation_activities = list(
                mongodb[workflow_set].find({"type": "nmdc:MetagenomeAnnotation"}, batch_size=100)
            )
            # TODO test this and make sure it works as expected
            # this undoes the pagination that existed before
            with click.progressbar(annotation_activities, length=len(annotation_activities)) as bar:
                pipeline.load(
                    db,
                    bar,
                    pipeline.load_mg_annotation,
                    WorkflowActivityTypeEnum.metagenome_annotation.value,
                    annotations=mongodb["functional_annotation_agg"],
                    function_limit=function_limit,
                )

        except Exception:
            logger.exception("Failed during annotation ingest.")
        finally:
            db.commit()

    else:
        logger.info("Skipping mg annotation ingest")

    try:
        logger.info("Loading metatranscriptome annotation...")
        pipeline.load(
            db,
            mongodb[workflow_set].find(
                {"type": WorkflowActivityTypeEnum.metatranscriptome_annotation.value}
            ),
            pipeline.load_mt_annotation,
            WorkflowActivityTypeEnum.metatranscriptome_annotation.value,
            annotations=mongodb["functional_annotation_agg"],
            function_limit=function_limit,
        )
    except Exception:
        logger.exception("Failed during metatranscriptome annotation ingest.")
    finally:
        db.commit()

    logger.info("Loading read qc...")
    pipeline.load(
        db,
        mongodb[workflow_set].find({"type": WorkflowActivityTypeEnum.reads_qc.value}),
        pipeline.load_reads_qc,
        WorkflowActivityTypeEnum.reads_qc.value,
    )
    db.commit()

    try:
        logger.info("Loading metaproteomic analysis...")
        pipeline.load(
            db,
            mongodb[workflow_set].find(
                {"type": WorkflowActivityTypeEnum.metaproteomic_analysis.value},
                no_cursor_timeout=True,
            ),
            pipeline.load_mp_analysis,
            WorkflowActivityTypeEnum.metaproteomic_analysis.value,
            annotations=mongodb["functional_annotation_agg"],
            function_limit=function_limit,
        )
        db.commit()
    except Exception:
        logger.exception("Failed during metap ingest.")
    finally:
        db.commit()

    logger.info("Loading metagenome assembly...")
    pipeline.load(
        db,
        mongodb[workflow_set].find({"type": WorkflowActivityTypeEnum.metagenome_assembly.value}),
        pipeline.load_mg_assembly,
        WorkflowActivityTypeEnum.metagenome_assembly.value,
    )
    db.commit()

    logger.info("Populating multiomics...")
    models.Biosample.populate_multiomics(db)
    db.commit()

    logger.info("Preprocessing envo term data")
    envo.build_envo_trees(db)

    logger.info("Loading search indices")
    search_index.load(db)
    db.commit()
