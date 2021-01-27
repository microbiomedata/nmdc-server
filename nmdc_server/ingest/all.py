import logging

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

    logger.info("Loading omics processing...")
    biosample_project = project.load(db, mongodb["omics_processing_set"].find())
    db.commit()

    logger.info("Loading biosamples...")
    biosample.load(db, mongodb["biosample_set"].find(), biosample_project)
    db.commit()

    logger.info("Loading metagenomes annotation...")
    pipeline.load(
        db,
        mongodb["activity_set"].find({"type": "nmdc:MetagenomeAnnotation"}),
        pipeline.load_mg_annotation,
        annotations=mongodb["raw.functional_annotation_set"],
    )
    db.commit()

    # logger.info("Loading read qc...")
    # pipeline.load(
    #     db,
    #     mongodb["activity_set"].find({"type": "nmdc:ReadQCAnalysisActivity"}),
    #     pipeline.load_reads_qc,
    # )
    # db.commit()

    logger.info("Loading metaproteomic analysis...")
    pipeline.load(
        db,
        mongodb["activity_set"].find({"type": "nmdc:MetaProteomicAnalysis"}),
        pipeline.load_mp_analysis,
    )
    db.commit()

    # logger.info("Loading metagenome assembly...")
    # pipeline.load(
    #     db,
    #     mongodb["activity_set"].find({"type": "nmdc:MetagenomeAssembly"}),
    #     pipeline.load_mg_assembly,
    # )
    # db.commit()
