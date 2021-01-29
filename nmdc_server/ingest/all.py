import logging

import click
from pymongo import MongoClient
from sqlalchemy.orm import Session

from nmdc_server.config import Settings
from nmdc_server.ingest import biosample, data_object, envo, pipeline, project, study

logger = logging.getLogger(__name__)


def load(db: Session):
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

    logger.info("Loading biosamples...")
    biosample.load(
        db, mongodb["biosample_set"].find(), omics_processing=mongodb["omics_processing_set"]
    )
    db.commit()

    logger.info("Loading omics processing...")
    project.load(db, mongodb["omics_processing_set"].find())
    db.commit()

    logger.info("Loading NOM analysis...")
    pipeline.load(
        db,
        mongodb["nom_analysis_activity_set"].find(),
        pipeline.load_nom_analysis,
    )
    db.commit()

    logger.info("Loading MAGs...")
    pipeline.load(
        db,
        mongodb["mags_activity_set"].find(),
        pipeline.load_mags,
    )
    db.commit()

    logger.info("Loading metagenome annotation...")
    cursor = mongodb["metagenome_annotation_activity_set"].find(
        no_cursor_timeout=True,
    )
    with click.progressbar(cursor, length=cursor.count()) as bar:
        pipeline.load(
            db,
            bar,
            pipeline.load_mg_annotation,
            annotations=mongodb["raw.functional_annotation_set"],
            function_limit=100,  # TODO: Remove to load all gene functions
        )
    db.commit()

    logger.info("Loading read qc...")
    pipeline.load(
        db,
        mongodb["read_QC_analysis_activity_set"].find(),
        pipeline.load_reads_qc,
    )
    db.commit()

    logger.info("Loading metaproteomic analysis...")
    pipeline.load(
        db,
        mongodb["metaproteomics_analysis_activity_set"].find(),
        pipeline.load_mp_analysis,
    )
    db.commit()

    logger.info("Loading metagenome assembly...")
    pipeline.load(
        db,
        mongodb["metagenome_assembly_set"].find(),
        pipeline.load_mg_assembly,
    )
    db.commit()
