import logging
from typing import Any, Dict, Iterator

import click
from pymongo import MongoClient
from pymongo.collection import Collection
from sqlalchemy.orm import Session

from nmdc_server import models
from nmdc_server.config import Settings
from nmdc_server.ingest import biosample, data_object, envo, omics_processing, pipeline, study

logger = logging.getLogger(__name__)


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


def load(db: Session, function_limit=None):
    """Ingest all data from the mongodb source.

    Optionally, you can limit the number of gene functions per omics_processing
    to allow for a faster ingest for testing.  The full result set takes several
    hours to process.

    This function is called both from the CLI (for development) and from the ingest
    celery function (in production).  Watch for warnings during ingest for ignored
    entities due to invalid foreign key references.
    """
    settings = Settings()
    if not (settings.mongo_user and settings.mongo_password):
        raise Exception("Please set NMDC_MONGO_USER and NMDC_MONGO_PASSWORD")

    client = MongoClient(
        host=settings.mongo_host, username=settings.mongo_user, password=settings.mongo_password
    )
    mongodb = client[settings.mongo_database]
    logger.info("Loading envo terms...")
    envo.load(db)
    db.commit()

    logger.info("Loading studies...")
    study.load(db, mongodb["study_set"].find())
    db.commit()

    logger.info("Loading data objects...")
    data_object.load(db, mongodb["data_object_set"].find())
    db.commit()

    # Only grab biosamples associated with studies we are ingesting.
    logger.info("Loading biosamples...")
    cursor = mongodb["biosample_set"].find(
        {
            "_study_id": {
                "$in": list(study.study_ids),
            },
        },
        no_cursor_timeout=True,
    )
    biosample.load(
        db,
        cursor,
        omics_processing=mongodb["omics_processing_set"],
    )
    db.commit()

    logger.info("Loading omics processing...")
    omics_processing.load(db, mongodb["omics_processing_set"].find())
    db.commit()

    logger.info("Loading metabolomics analysis...")
    pipeline.load(
        db,
        mongodb["metabolomics_analysis_activity_set"].find(),
        pipeline.load_metabolomics_analysis,
        "nmdc:MetabolomicsAnalysisActivity",
    )
    db.commit()

    logger.info("Loading read based analysis...")
    pipeline.load(
        db,
        mongodb["read_based_analysis_activity_set"].find(),
        pipeline.load_read_based_analysis,
        "nmdc:ReadbasedAnalysis",
    )
    db.commit()

    logger.info("Loading NOM analysis...")
    pipeline.load(
        db,
        mongodb["nom_analysis_activity_set"].find(),
        pipeline.load_nom_analysis,
        "nmdc:NomAnalysisActivity",
    )
    db.commit()

    logger.info("Loading MAGs...")
    pipeline.load(
        db,
        mongodb["mags_activity_set"].find(),
        pipeline.load_mags,
        "nmdc:MAGsAnalysisActivity",
    )
    db.commit()

    try:
        # This section has its own subprogress bar because it takes several
        # hours to ingest all of the gene function products from the metag
        # workflows.
        logger.info("Loading metagenome annotation...")

        # This has historically been fast, but it is only for the progress bar.
        # It can be removed if it becomes slow.
        count = mongodb["metagenome_annotation_activity_set"].find().count()
        iterator = paginate_cursor(
            mongodb["metagenome_annotation_activity_set"],
            page_size=1,  # prevent cursor from timing out
            no_cursor_timeout=True,
        )
        with click.progressbar(iterator, length=count) as bar:
            pipeline.load(
                db,
                bar,
                pipeline.load_mg_annotation,
                "nmdc:MetagenomeAnnotation",
                annotations=mongodb["raw.functional_annotation_set"],
                function_limit=function_limit,
            )
    except Exception:
        logger.exception("Failed during metag ingest.")
    finally:
        db.commit()

    logger.info("Loading read qc...")
    pipeline.load(
        db,
        mongodb["read_QC_analysis_activity_set"].find(),
        pipeline.load_reads_qc,
        "nmdc:ReadQCAnalysisActivity",
    )
    db.commit()

    try:
        logger.info("Loading metaproteomic analysis...")
        pipeline.load(
            db,
            mongodb["metaproteomics_analysis_activity_set"].find(
                no_cursor_timeout=True,
            ),
            pipeline.load_mp_analysis,
            "nmdc:MetaProteomicAnalysis",
        )
        db.commit()
    except Exception:
        logger.exception("Failed during metap ingest.")
    finally:
        db.commit()

    logger.info("Loading metagenome assembly...")
    pipeline.load(
        db,
        mongodb["metagenome_assembly_set"].find(),
        pipeline.load_mg_assembly,
        "nmdc:MetagenomeAssembly",
    )
    db.commit()

    # all the data is loaded, so trigger denormalization updates
    models.MGAGeneFunctionAggregation.populate(db)
    db.commit()

    models.MetaPGeneFunctionAggregation.populate(db)
    db.commit()

    models.Biosample.populate_multiomics(db)
    db.commit()
