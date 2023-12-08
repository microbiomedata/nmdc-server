from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, cast
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Query, Session

from nmdc_server import aggregations, bulk_download_schema, models, query, schemas
from nmdc_server.data_object_filters import get_local_data_url
from nmdc_server.logger import get_logger

logger = get_logger(__name__)
NumericValue = query.NumericValue
T = TypeVar("T", bound=models.Base)


# See: https://docs.djangoomics_processing.com/en/3.0/ref/models/querysets/#get-or-create
def get_or_create(
    db: Session, model: Type[T], defaults: Optional[Dict[str, Any]] = None, **kwargs
) -> Tuple[T, bool]:
    """Get a model instance or create a new one if it does not exist."""
    instance = db.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict(**kwargs)
        params.update(defaults or {})
        instance = model(**params)  # type: ignore
        db.add(instance)
        return instance, True


# summaries
def get_database_summary(db: Session) -> schemas.DatabaseSummary:
    gene_function_count = db.query(models.GeneFunction).count()
    gene_function = schemas.TableSummary(
        total=gene_function_count,
        attributes={
            "id": schemas.AttributeSummary(
                count=gene_function_count,
                type="string",
            )
        },
    )
    return schemas.DatabaseSummary(
        study=aggregations.get_table_summary(db, models.Study),
        omics_processing=aggregations.get_table_summary(db, models.OmicsProcessing),
        biosample=aggregations.get_table_summary(db, models.Biosample),
        data_object=aggregations.get_table_summary(db, models.DataObject),
        reads_qc=aggregations.get_table_summary(db, models.ReadsQC),
        metagenome_assembly=aggregations.get_table_summary(db, models.MetagenomeAssembly),
        metagenome_annotation=aggregations.get_table_summary(db, models.MetagenomeAnnotation),
        metaproteomic_analysis=aggregations.get_table_summary(db, models.MetaproteomicAnalysis),
        mags_analysis=aggregations.get_table_summary(db, models.MAGsAnalysis),
        read_based_analysis=aggregations.get_table_summary(db, models.ReadBasedAnalysis),
        nom_analysis=aggregations.get_table_summary(db, models.NOMAnalysis),
        metabolomics_analysis=aggregations.get_table_summary(db, models.MetabolomicsAnalysis),
        metatranscriptome=aggregations.get_table_summary(db, models.Metatranscriptome),
        gene_function=gene_function,
    )


def get_aggregated_stats(db: Session) -> schemas.AggregationSummary:
    return aggregations.get_aggregation_summary(db)


def text_search(db: Session, terms: str, limit: int) -> List[models.SearchIndex]:
    searchtext = f"%{terms.lower()}%"
    facets = (
        db.query(models.SearchIndex)
        .filter(models.SearchIndex.value.ilike(searchtext))
        .order_by(models.SearchIndex.count.desc())
        .limit(limit)
        .all()
    )
    return facets


def get_environmental_sankey(
    db: Session, query: query.BiosampleQuerySchema
) -> List[schemas.EnvironmentSankeyAggregation]:
    return aggregations.get_sankey_aggregation(db, query)


def get_environmental_geospatial(
    db: Session, query: query.BiosampleQuerySchema
) -> List[schemas.EnvironmentGeospatialAggregation]:
    return aggregations.get_geospatial_aggregation(db, query)


# study
def get_study(db: Session, study_id: str) -> Optional[models.Study]:
    return search_study(
        db,
        [{"table": "study", "field": "id", "value": study_id}],  # type: ignore
    ).first()


def get_study_image(db: Session, study_id: str) -> Optional[bytes]:
    study = db.query(models.Study).get(study_id)
    if study is not None:
        return study.image
    return None


def get_doi(db: Session, doi_id: str) -> Optional[models.DOIInfo]:
    doi = db.query(models.DOIInfo).get(doi_id)
    return doi


def create_study(db: Session, study: schemas.StudyCreate) -> models.Study:
    study_dict = study.dict()

    websites = study_dict.pop("principal_investigator_websites")

    db_study = models.Study(**study_dict)

    for url in websites:
        website, _ = get_or_create(db, models.Website, url=url)
        study_website = models.StudyWebsite(website=website)
        db_study.principal_investigator_websites.append(study_website)  # type: ignore

    db.add(db_study)
    db.commit()
    db.refresh(db_study)
    return db_study


def delete_study(db: Session, study: models.Study) -> None:
    db.delete(study)
    db.commit()


def search_study(db: Session, conditions: List[query.ConditionSchema]) -> Query:
    return query.StudyQuerySchema(conditions=conditions).execute(db)


def facet_study(
    db: Session, attribute: str, conditions: List[query.ConditionSchema]
) -> query.FacetResponse:
    facets = query.StudyQuerySchema(conditions=conditions).facet(db, attribute)
    return query.FacetResponse(facets=facets)


def binned_facet_study(
    db: Session,
    attribute: str,
    conditions: List[query.ConditionSchema],
    **kwargs,
) -> query.BinnedFacetResponse:
    bins, facets = query.StudyQuerySchema(conditions=conditions).binned_facet(
        db, attribute, **kwargs
    )
    return query.BinnedFacetResponse(bins=bins, facets=facets)


# omics_processing
def get_omics_processing(db: Session, omics_processing_id: str) -> Optional[models.OmicsProcessing]:
    return (
        db.query(models.OmicsProcessing)
        .filter(models.OmicsProcessing.id == omics_processing_id)
        .first()
    )


def create_omics_processing(
    db: Session, omics_processing: schemas.OmicsProcessingCreate
) -> models.OmicsProcessing:
    db_omics_processing = models.OmicsProcessing(**omics_processing.dict())
    db.add(db_omics_processing)
    db.commit()
    db.refresh(db_omics_processing)
    return db_omics_processing


def delete_omics_processing(db: Session, omics_processing: models.OmicsProcessing) -> None:
    db.delete(omics_processing)
    db.commit()


def search_omics_processing(db: Session, conditions: List[query.ConditionSchema]) -> Query:
    return query.OmicsProcessingQuerySchema(conditions=conditions).execute(db)


def facet_omics_processing(
    db: Session, attribute: str, conditions: List[query.ConditionSchema]
) -> query.FacetResponse:
    facets = query.OmicsProcessingQuerySchema(conditions=conditions).facet(db, attribute)
    return query.FacetResponse(facets=facets)


def binned_facet_omics_processing(
    db: Session,
    attribute: str,
    conditions: List[query.ConditionSchema],
    **kwargs,
) -> query.BinnedFacetResponse:
    bins, facets = query.OmicsProcessingQuerySchema(conditions=conditions).binned_facet(
        db, attribute, **kwargs
    )
    return query.BinnedFacetResponse(bins=bins, facets=facets)


def list_omics_processing_data_objects(db: Session, id: str) -> Query:
    return (
        db.query(models.DataObject)
        .join(models.omics_processing_output_association)
        .filter(models.omics_processing_output_association.c.omics_processing_id == id)
    )


def list_ko_terms_for_module(db: Session, module: str) -> List[str]:
    q = db.query(models.KoTermToModule.term).filter(models.KoTermToModule.module.ilike(module))
    return [row[0] for row in q]


def list_ko_terms_for_pathway(db: Session, pathway: str) -> List[str]:
    q = db.query(models.KoTermToPathway.term).filter(models.KoTermToPathway.pathway.ilike(pathway))
    return [row[0] for row in q]


def kegg_text_search(db: Session, query: str, limit: int) -> List[models.KoTermText]:
    q = (
        db.query(models.KoTermText)
        .filter(models.KoTermText.text.ilike(f"%{query}%") | models.KoTermText.term.ilike(query))
        .order_by(models.KoTermText.term)
        .limit(limit)
    )
    return list(q)


# biosample
def get_biosample(db: Session, biosample_id: str) -> Optional[models.Biosample]:
    return db.query(models.Biosample).filter(models.Biosample.id == biosample_id).first()


def create_biosample(db: Session, biosample: schemas.BiosampleCreate) -> models.Biosample:
    db_biosample = models.Biosample(**biosample.dict())
    db.add(db_biosample)
    db.commit()
    db.refresh(db_biosample)
    return db_biosample


def delete_biosample(db: Session, biosample: models.Biosample) -> None:
    db.delete(biosample)
    db.commit()


def search_biosample(
    db: Session,
    conditions: List[query.ConditionSchema],
    data_object_filter: List[query.DataObjectFilter],
) -> Query:
    return query.BiosampleQuerySchema(
        conditions=conditions, data_object_filter=data_object_filter
    ).execute(db)


def facet_biosample(
    db: Session, attribute: str, conditions: List[query.ConditionSchema], **kwargs
) -> query.FacetResponse:
    facets = query.BiosampleQuerySchema(conditions=conditions).facet(db, attribute)
    return query.FacetResponse(facets=facets)


def binned_facet_biosample(
    db: Session,
    attribute: str,
    conditions: List[query.ConditionSchema],
    **kwargs,
) -> query.BinnedFacetResponse:
    bins, facets = query.BiosampleQuerySchema(conditions=conditions).binned_facet(
        db, attribute, **kwargs
    )
    return query.BinnedFacetResponse(bins=bins, facets=facets)


# data object
def get_data_object(db: Session, data_object_id: str) -> Optional[models.DataObject]:
    return db.query(models.DataObject).filter(models.DataObject.id == data_object_id).first()


def create_data_object(db: Session, data_object: schemas.DataObjectCreate) -> models.DataObject:
    db_data_object = models.DataObject(**data_object.dict())
    db.add(db_data_object)
    db.commit()
    db.refresh(db_data_object)
    return db_data_object


def delete_data_object(db: Session, data_object: models.DataObject) -> None:
    db.delete(data_object)
    db.commit()


def aggregate_data_object_by_workflow(
    db: Session, conditions: List[query.ConditionSchema]
) -> schemas.DataObjectAggregation:
    return aggregations.get_data_object_aggregation(db, conditions)


# principal investigator
def get_pi_image(db: Session, principal_investigator_id: UUID) -> Optional[bytes]:
    pi = db.query(models.PrincipalInvestigator).get(principal_investigator_id)
    if pi is not None:
        return pi.image
    return None


def create_file_download(
    db: Session, file_download: schemas.FileDownloadCreate
) -> models.FileDownload:
    db_file_download = models.FileDownload(**file_download.dict())
    db.add(db_file_download)
    db.commit()
    db.refresh(db_file_download)
    return db_file_download


def construct_zip_file_path(data_object: models.DataObject) -> str:
    """Return a path inside the zip file for the data object."""
    # TODO:
    #   - Users will most likely want more descriptive folder names
    #   - Add metadata for parent entities in the zip file
    #   - We probably want to reference the workflow activity but that
    #     involves a complicated query... need a way to join that information
    #     in the original query (possibly in the sqlalchemy relationship)
    omics_processing = data_object.omics_processing
    biosamples = cast(Optional[list[models.Biosample]], omics_processing.biosample_inputs)

    def safe_name(name: str) -> str:
        return name.replace("/", "_").replace("\\", "_").replace(":", "_")

    op_name = safe_name(omics_processing.id)

    if biosamples:
        biosample_name = ",".join([safe_name(biosample.id) for biosample in biosamples])
        study = biosamples[0].study
    else:
        # Some emsl omics_processing are missing biosamples
        biosample_name = "unknown"
        study = omics_processing.study

    study_name = safe_name(study.id)
    da_name = safe_name(data_object.name)
    return f"{study_name}/{biosample_name}/{op_name}/{da_name}"


def create_bulk_download(
    db: Session, bulk_download: bulk_download_schema.BulkDownloadCreate
) -> Optional[models.BulkDownload]:
    data_object_query = query.DataObjectQuerySchema(
        conditions=bulk_download.conditions,
        data_object_filter=bulk_download.filter,
    )
    try:
        bulk_download_model = models.BulkDownload(**bulk_download.dict())
        db.add(bulk_download_model)

        has_files = False
        for data_object in data_object_query.execute(db):
            if data_object.url is None:
                logger.warning("Data object url is empty in bulk download")
                continue

            has_files = True

            db.add(
                models.BulkDownloadDataObject(
                    bulk_download=bulk_download_model,
                    data_object=data_object,
                    path=construct_zip_file_path(data_object),
                )
            )

        if not has_files:
            db.rollback()
            return None

        db.commit()
        return bulk_download_model

    except Exception:
        db.rollback()
        raise


def get_zip_download(db: Session, id: UUID) -> Optional[str]:
    """Return a download table compatible with mod_zip."""
    bulk_download = db.query(models.BulkDownload).get(id)
    if bulk_download is None:
        return None
    content = []

    for file in bulk_download.files:  # type: ignore
        data_object = file.data_object
        url = get_local_data_url(data_object.url)
        if url is None:
            logger.warning(f"Data object url for {file.path} was {data_object.url}")
            continue

        # TODO: add crc checksums to support retries
        # TODO: add directory structure and metadata
        file_size_string = data_object.file_size_bytes if data_object.file_size_bytes else ""
        content.append(f"- {file_size_string} {url} {file.path}")

    return "\n".join(content) + "\n"


def get_or_create_user(db: Session, user: schemas.User) -> models.User:
    """Create a user if not present"""
    db_user, created = get_or_create(db, models.User, defaults=user.dict(), orcid=user.orcid)
    if created:
        db.commit()
    return db_user


def update_user(db: Session, user: schemas.User) -> Optional[models.User]:
    db_user = db.query(models.User).get(user.id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    db_user.is_admin = user.is_admin
    db.commit()
    return db_user


def update_submission_lock(db: Session, submission_id: str):
    """Update the timestamp for a locked submission."""
    submission_record = db.query(models.SubmissionMetadata).get(submission_id)
    if not submission_record:
        # Throw a different error, or accept different params
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    submission_record.lock_updated = datetime.utcnow()
    db.commit()


def try_get_submission_lock(db: Session, submission_id: str, user_id: str) -> bool:
    """
    Try to obtain the lock for a submission.

    Returns True if the given user obtains the lock, otherwise False.
    If the result is `True`, a side effect of this function is updating the submission with the new
    lock owner.
    """

    # Ensure the requested records exist
    submission_record = db.query(models.SubmissionMetadata).get(submission_id)
    if not submission_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    user_record = db.query(models.User).get(user_id)
    if not user_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    current_lock_holder = submission_record.locked_by
    if not current_lock_holder or current_lock_holder.id == user_id:
        # Either the given user already has the lock, or no one does
        submission_record.locked_by = user_record
        submission_record.lock_updated = datetime.utcnow()
        db.commit()
        return True
    else:
        # Someone else is holding the lock
        if submission_record.lock_updated:
            # Compare current time to last edit
            seconds_since_last_lock_update = (
                datetime.utcnow() - submission_record.lock_updated
            ).total_seconds()
            # A user can hold the lock for 30 minutes without making edits
            if seconds_since_last_lock_update > (60 * 30):
                submission_record.locked_by = user_record
                submission_record.lock_updated = datetime.utcnow()
                db.commit()
                return True
            else:
                # Someone else holds the lock, but there's no timestamp
                # Ensure that there's a timestamp on the lock.
                submission_record.lock_updated = datetime.utcnow()
    return False


def release_submission_lock(db: Session, submission_id: str):
    submission = db.query(models.SubmissionMetadata).get(submission_id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    submission.locked_by = None  # type: ignore
    db.commit()
