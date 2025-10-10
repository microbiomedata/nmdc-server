import re
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, cast
from uuid import UUID

from fastapi import HTTPException, status
from nmdc_schema.nmdc import SubmissionStatusEnum
from sqlalchemy import and_
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql import func

from nmdc_server import aggregations, bulk_download_schema, models, query, schemas
from nmdc_server.config import settings
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
        instance = model(**params)
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
        metatranscriptome_assembly=aggregations.get_table_summary(
            db, models.MetatranscriptomeAssembly
        ),
        metatranscriptome_annotation=aggregations.get_table_summary(
            db, models.MetatranscriptomeAnnotation
        ),
        metaproteomic_analysis=aggregations.get_table_summary(db, models.MetaproteomicAnalysis),
        mags_analysis=aggregations.get_table_summary(db, models.MAGsAnalysis),
        read_based_analysis=aggregations.get_table_summary(db, models.ReadBasedAnalysis),
        nom_analysis=aggregations.get_table_summary(db, models.NOMAnalysis),
        metabolomics_analysis=aggregations.get_table_summary(db, models.MetabolomicsAnalysis),
        metatranscriptome=aggregations.get_table_summary(db, models.Metatranscriptome),
        gene_function=gene_function,
    )


def get_admin_stats(db: Session) -> schemas.AdminStats:
    r"""
    Compiles statistics designed to be consumed by Data Portal/Submission Portal administrators.
    """

    distinct_orcids_subquery = db.query(func.distinct(models.User.orcid)).subquery()
    num_distinct_orcids = db.query(func.count()).select_from(distinct_orcids_subquery).scalar()

    return schemas.AdminStats(
        num_user_accounts=num_distinct_orcids,
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
    study = db.get(models.Study, study_id)  # type: ignore  # type: ignore
    if study is not None:
        return study.image
    return None


def get_doi(db: Session, doi_id: str) -> Optional[models.DOIInfo]:
    doi = db.get(models.DOIInfo, doi_id)  # type: ignore
    return doi


def create_study(db: Session, study: schemas.StudyCreate) -> models.Study:
    study_dict = study.dict()

    websites = study_dict.pop("principal_investigator_websites")

    db_study = models.Study(**study_dict)

    for url in websites:
        website, _ = get_or_create(db, models.Website, url=url)
        study_website = models.StudyWebsite(website=website)
        db_study.principal_investigator_websites.append(study_website)

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


def search_omics_processing_for_biosamples(
    db: Session, conditions: List[query.ConditionSchema], biosample_ids: List[UUID]
) -> Query:
    return query.OmicsProcessingQuerySchema(
        conditions=conditions
    ).omics_processing_for_biosample_ids(db, biosample_ids)


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


# KEGG
def get_pathway_prefix(term) -> Optional[str]:
    pathway_prefixes = set(["map", "ko", "ec", "rn", "org"])
    pathway_re = f"^({'|'.join(re.escape(p) for p in pathway_prefixes)})"
    match = re.match(pathway_re, term)
    return match.group(0) if match else None


def list_ko_terms_for_module(db: Session, module: str) -> List[str]:
    q = db.query(models.KoTermToModule.term).filter(models.KoTermToModule.module.ilike(module))
    return [row[0] for row in q]


def list_ko_terms_for_pathway(db: Session, pathway: str) -> List[str]:
    q = db.query(models.KoTermToPathway.term).filter(models.KoTermToPathway.pathway.ilike(pathway))
    return [row[0] for row in q]


def kegg_text_search(db: Session, query: str, limit: int) -> List[models.KoTermText]:
    pathway_prefix = get_pathway_prefix(query)
    term = query.replace(pathway_prefix, "map") if pathway_prefix else query
    q = (
        db.query(models.KoTermText)
        .filter(models.KoTermText.text.ilike(f"%{term}%") | models.KoTermText.term.ilike(term))
        .order_by(models.KoTermText.term)
        .limit(limit)
    )
    results = list(q)
    if pathway_prefix:
        default_pathway_prefix = "map"
        # Transform pathway results to match given prefix. They are ingested with the
        # 'map' prefix, but can searched for with various other prefixes.
        for term_text in results:
            if term_text.term.startswith(default_pathway_prefix):
                term_text.term = term_text.term.replace(default_pathway_prefix, pathway_prefix)
            term_text.text = term_text.text.replace(default_pathway_prefix, pathway_prefix)
    return results


def cog_text_search(db: Session, query: str, limit: int) -> List[models.CogTermText]:
    q = (
        db.query(models.CogTermText)
        .filter(
            models.CogTermText.text.ilike(f"%{query}%")
            | models.CogTermText.term.ilike(f"%{query}%")
        )
        .order_by(models.CogTermText.term)
        .limit(limit)
    )
    return list(q)


def pfam_text_search(db: Session, query: str, limit: int) -> List[models.PfamTermText]:
    q = (
        db.query(models.PfamTermText)
        .filter(
            models.PfamTermText.text.ilike(f"%{query}%")
            | models.PfamTermText.term.ilike(f"%{query}%")
        )
        .order_by(models.PfamTermText.term)
        .limit(limit)
    )
    return list(q)


def go_text_search(db: Session, query: str, limit: int) -> List[models.GoTermText]:
    q = (
        db.query(models.GoTermText)
        .filter(
            models.GoTermText.text.ilike(f"%{query}%") | models.GoTermText.term.ilike(f"%{query}%")
        )
        .order_by(models.GoTermText.term)
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


def get_data_object_counts(db: Session, data_object_ids: list[str]) -> defaultdict[str, int]:
    labels = ("data_object_id", "count")
    file_downloads = (
        db.query(models.FileDownload.data_object_id.label(labels[0]), func.count().label(labels[1]))
        .filter(models.FileDownload.data_object_id.in_(data_object_ids))
        .group_by(models.FileDownload.data_object_id)
        .order_by(models.FileDownload.data_object_id)
    )
    bulk_downloads = (
        db.query(
            models.BulkDownloadDataObject.data_object_id.label(labels[0]),
            func.count().label(labels[1]),
        )
        .filter(models.BulkDownloadDataObject.data_object_id.in_(data_object_ids))
        .group_by(models.BulkDownloadDataObject.data_object_id)
        .order_by(models.BulkDownloadDataObject.data_object_id)
    )
    all_counts = file_downloads.union(bulk_downloads)
    counts: defaultdict[str, int] = defaultdict(int)
    for row in all_counts:
        counts[row[0]] += row[1]
    return counts


def search_biosample(
    db: Session,
    conditions: List[query.ConditionSchema],
    data_object_filter: List[query.DataObjectFilter],
    prefetch_omics_processing_data: bool = False,
) -> Query:
    return query.BiosampleQuerySchema(
        conditions=conditions, data_object_filter=data_object_filter
    ).execute(db, prefetch_omics_processing_data)


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
    pi = db.get(models.PrincipalInvestigator, principal_investigator_id)  # type: ignore
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
    if not data_object.omics_processings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data object has no associated omics processings.",
        )
    omics_processing = data_object.omics_processings[0]
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


def replace_nersc_data_url_prefix(url: str, replacement_url_prefix: str) -> str:
    """Conditionally replace the beginning portion of the specified URL.

    If the URL refers to a data file hosted at NERSC, this function will return
    a URL in which the beginning portion of the URL has been replaced with the
    specified replacement string.

    This can be used to optimize the URL for different use cases. For example,
    the ZipStreamer instance in this application's stack could take advantage of
    a URL that points directly to a data proxy that is not exposed to the Internet,
    whereas a web browser might require a URL pointing to a Kubernetes ingress that
    _is_ exposed directly to the Internet (which might lead to that same private
    data proxy, but not as directly).

    # Test: NERSC data URL (prefix gets replaced).
    >>> replace_nersc_data_url_prefix(
    ...     "https://data.microbiomedata.org/data/some/file.txt",
    ...     "https://www.example.com/path/to"
    ... )
    'https://www.example.com/path/to/some/file.txt'

    # Test: Not a NERSC data URL (prefix does not get replaced).
    >>> replace_nersc_data_url_prefix(
    ...     "https://other.microbiomedata.org/data/some/file.txt",
    ...     "https://www.example.com/path/to"
    ... )
    'https://other.microbiomedata.org/data/some/file.txt'
    """

    nersc_data_url_prefix = r"https://data.microbiomedata.org/data"
    if url.startswith(nersc_data_url_prefix):
        return url.replace(nersc_data_url_prefix, replacement_url_prefix, 1)
    return url


def get_zip_download(db: Session, id: UUID) -> Dict[str, Any]:
    """Return a zip file descriptor compatible with zipstreamer."""
    bulk_download = db.get(models.BulkDownload, id)  # type: ignore
    if bulk_download is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bulk download not found")
    if bulk_download.expired:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Bulk download expired")
    zip_file_descriptor: Dict[str, Any] = {"suggestedFilename": "archive.zip"}
    file_descriptions: List[Dict[str, str]] = []

    for file in bulk_download.files:
        data_object = file.data_object
        if data_object.url is None:
            logger.warning(f"Data object url for {file.path} was {data_object.url}")
            continue

        # Overwrite the prefix of the URL if it refers to a data file hosted at NERSC.
        url = replace_nersc_data_url_prefix(
            url=data_object.url,
            replacement_url_prefix=settings.zip_streamer_nersc_data_base_url
        )
        file_descriptions.append({"url": url, "zipPath": file.path})

    zip_file_descriptor["files"] = file_descriptions

    bulk_download.expired = True
    db.commit()

    return zip_file_descriptor


def get_user(db: Session, user_id: str) -> Optional[models.User]:
    """Get a user by ID."""
    return db.get(models.User, user_id)  # type: ignore


def get_or_create_user(db: Session, user: schemas.User) -> models.User:
    """Create a user if not present"""
    db_user, created = get_or_create(db, models.User, defaults=user.dict(), orcid=user.orcid)
    if created:
        db.commit()
    return db_user


def update_user(db: Session, user: schemas.User) -> Optional[models.User]:
    db_user = db.get(models.User, user.id)  # type: ignore
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    db_user.is_admin = user.is_admin
    db_user.email = user.email
    db.commit()
    return db_user


def add_invalidated_token(db: Session, token: str) -> None:
    """Add a token to the invalidated token table."""
    invalidated = models.InvalidatedToken(token=token)
    db.add(invalidated)
    db.commit()


def get_invalidated_token(db: Session, token: str) -> Optional[models.InvalidatedToken]:
    """Get an invalidated token by token."""
    return db.get(models.InvalidatedToken, token)  # type: ignore


def create_authorization_code(
    db: Session, user: models.User, redirect_uri: str
) -> models.AuthorizationCode:
    """Generate an authorization code tied to a user and redirect URI."""
    code = models.AuthorizationCode(user_id=user.id, redirect_uri=redirect_uri)
    db.add(code)
    db.commit()
    return code


def get_authorization_code(db: Session, code: str) -> Optional[models.AuthorizationCode]:
    """Get an authorization code by code."""
    return db.get(models.AuthorizationCode, code)  # type: ignore


def update_submission_lock(db: Session, submission_id: str):
    """Update the timestamp for a locked submission."""
    submission_record = db.get(models.SubmissionMetadata, submission_id)  # type: ignore
    if not submission_record:
        # Throw a different error, or accept different params
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    submission_record.lock_updated = datetime.now(UTC)
    db.commit()


def try_get_submission_lock(db: Session, submission_id: str, user_id: str) -> bool:
    """
    Try to obtain the lock for a submission.

    Returns True if the given user obtains the lock, otherwise False.
    If the result is `True`, a side effect of this function is updating the submission with the new
    lock owner.
    """

    # Ensure the requested records exist
    submission_record = db.get(models.SubmissionMetadata, submission_id)  # type: ignore
    if not submission_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    user_record: Optional[models.User] = db.get(models.User, user_id)  # type: ignore
    if not user_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check that the user has sufficient permissions to obtain the lock
    if not (user_record.is_admin or can_read_submission(db, submission_id, user_record.orcid)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission to obtain lock",
        )

    current_lock_holder = submission_record.locked_by
    if not current_lock_holder or current_lock_holder.id == user_id:
        # Either the given user already has the lock, or no one does
        submission_record.locked_by = user_record
        submission_record.lock_updated = datetime.now(UTC)
        db.commit()
        return True
    else:
        # Someone else is holding the lock
        if submission_record.lock_updated:
            # Compare current time to last edit
            # Note that currently this application always uses datetime.now(UTC)
            # to update this field. Currently the corresponding column in postgres
            # is not actually timezone aware, so the value we get back out must have
            # the timezone information added back.
            # TODO: create a migration to make the Postgres column timezone-aware, and
            # remove this call to `replace`
            lock_updated_utc = submission_record.lock_updated.replace(tzinfo=UTC)
            seconds_since_last_lock_update = (datetime.now(UTC) - lock_updated_utc).total_seconds()
            # A user can hold the lock for 30 minutes without making edits
            if seconds_since_last_lock_update > (60 * 30):
                submission_record.locked_by = user_record
                submission_record.lock_updated = datetime.now(UTC)
                db.commit()
                return True
        else:
            # Someone else holds the lock, but there's no timestamp
            # Ensure that there's a timestamp on the lock.
            submission_record.lock_updated = datetime.now(UTC)
    return False


def release_submission_lock(db: Session, submission_id: str):
    submission = db.get(models.SubmissionMetadata, submission_id)  # type: ignore
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    submission.locked_by = None
    db.commit()


#############################
# SUBMISSION ACCESS CONTROL #
#############################
read_roles = [
    models.SubmissionEditorRole.editor,
    models.SubmissionEditorRole.metadata_contributor,
    models.SubmissionEditorRole.owner,
    models.SubmissionEditorRole.viewer,
    models.SubmissionEditorRole.reviewer,
]

metadata_edit_roles = [
    models.SubmissionEditorRole.editor,
    models.SubmissionEditorRole.metadata_contributor,
    models.SubmissionEditorRole.owner,
]

context_edit_roles = [
    models.SubmissionEditorRole.editor,
    models.SubmissionEditorRole.owner,
]

contributors_edit_roles = [
    models.SubmissionEditorRole.owner,
]


def get_submission_for_user(
    db: Session,
    submission_id: str,
    requester: models.User,
    *,
    allowed_roles: list[models.SubmissionEditorRole] | None = None,
) -> models.SubmissionMetadata:
    """Get a submission by ID and additionally check if the requesting user has one of the allowed
    roles on the submission.

    :raise HTTPException: If the submission does not exist or if the user does not have one of the
        allowed roles on the submission.

    :param db: The database session.
    :param submission_id: The ID of the submission to retrieve.
    :param requester: The user requesting the submission.
    :param allowed_roles: A list of allowed roles that the user must have on the submission. If
        None, no role check is performed.
    """
    submission: Optional[models.SubmissionMetadata] = db.get(  # type: ignore
        models.SubmissionMetadata, submission_id
    )
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    if allowed_roles and not requester.is_admin:
        # If the user is not an admin, check if they have one of the allowed roles
        # on the submission.
        role = get_submission_role(db, submission_id, requester.orcid)
        if not role or models.SubmissionEditorRole(role.role) not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permission to complete this action",
            )
    return submission


def get_submission_role(
    db: Session, submission_id: str, user_orcid: str
) -> Optional[models.SubmissionRole]:
    role = (
        db.query(models.SubmissionRole)
        .filter(
            and_(
                models.SubmissionRole.user_orcid == user_orcid,
                models.SubmissionRole.submission_id == submission_id,
            )
        )
        .first()
    )
    return role


def can_read_submission(db: Session, submission_id: str, user_orcid: str) -> Optional[bool]:
    role = (
        db.query(models.SubmissionRole)
        .filter(
            and_(
                models.SubmissionRole.user_orcid == user_orcid,
                models.SubmissionRole.submission_id == submission_id,
            )
        )
        .first()
    )
    submission: Optional[models.SubmissionMetadata] = db.get(  # type: ignore
        models.SubmissionMetadata, submission_id
    )
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    return (role and models.SubmissionEditorRole(role.role) in read_roles) is True


def can_edit_entire_submission(db: Session, submission_id: str, user_orcid: str) -> Optional[bool]:
    role = (
        db.query(models.SubmissionRole)
        .filter(
            and_(
                models.SubmissionRole.user_orcid == user_orcid,
                models.SubmissionRole.submission_id == submission_id,
            )
        )
        .first()
    )
    submission: Optional[models.SubmissionMetadata] = db.get(  # type: ignore
        models.SubmissionMetadata, submission_id
    )
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    return (role and models.SubmissionEditorRole(role.role) in contributors_edit_roles) is True


def get_submissions_for_user(
    db: Session,
    user: models.User,
    column_sort: str,
    order: str,
    is_test_submission_filter: Optional[bool] = None,
):
    """Return all submissions that a user has permission to view."""
    column = (
        models.User.name
        if column_sort == "author.name"
        else getattr(models.SubmissionMetadata, column_sort)
    )

    all_submissions = (
        db.query(models.SubmissionMetadata)
        .join(models.User, models.SubmissionMetadata.author_id == models.User.id)
        .order_by(column.asc() if order == "asc" else column.desc())
    )

    if is_test_submission_filter != None:
        all_submissions = all_submissions.filter(
            models.SubmissionMetadata.is_test_submission == is_test_submission_filter
        )

    if user.is_admin:
        return all_submissions

    permitted_submissions = all_submissions.outerjoin(models.SubmissionRole)
    permitted_submissions = permitted_submissions.filter(
        models.SubmissionRole.user_orcid == user.orcid
    )
    return permitted_submissions


def get_query_for_all_submissions(db: Session):
    r"""
    Returns a SQLAlchemy query that can be used to retrieve all submissions.

    Reference: https://fastapi.tiangolo.com/tutorial/sql-databases/#crud-utils
    Reference: https://docs.sqlalchemy.org/en/14/orm/session_basics.html
    """
    all_submissions = db.query(models.SubmissionMetadata).order_by(
        models.SubmissionMetadata.created.desc()
    )
    return all_submissions


def get_query_for_submitted_pending_review_submissions(db: Session):
    r"""
    Returns a SQLAlchemy query that can be used to retrieve submissions pending review.

    Reference: https://fastapi.tiangolo.com/tutorial/sql-databases/#crud-utils
    Reference: https://docs.sqlalchemy.org/en/14/orm/session_basics.html
    """
    submitted_pending_review = db.query(models.SubmissionMetadata).filter(
        models.SubmissionMetadata.status == SubmissionStatusEnum.SubmittedPendingReview.text
    )
    return submitted_pending_review


def get_roles_for_submission(
    db: Session, submission: models.SubmissionMetadata
) -> List[models.SubmissionRole]:
    return (
        db.query(models.SubmissionRole)
        .filter(models.SubmissionRole.submission_id == submission.id)
        .all()
    )


def update_submission_contributor_roles(
    db: Session, submission: models.SubmissionMetadata, new_permissions: Dict[str, str]
):
    """
    Update permissions for a given submission.

    new_permissions is a dictionary that maps ORCID iDs to permission level values.
    This function ignores and change to or absence of the author's permission level
    """
    submission_roles: List[models.SubmissionRole] = get_roles_for_submission(db, submission)

    for role in submission_roles:
        if role.user_orcid in new_permissions:
            if (
                role.role != new_permissions[role.user_orcid]
                and role.role != models.SubmissionEditorRole.owner
            ):
                # Don't edit owner roles
                role.role = models.SubmissionEditorRole(new_permissions[role.user_orcid])
        elif role.role != models.SubmissionEditorRole.owner:
            # Don't delete owner roles
            db.delete(role)

    new_user_role_needed = set(new_permissions) - set(
        [role.user_orcid for role in submission_roles]
    )

    for orcid in new_user_role_needed:
        role_value = models.SubmissionEditorRole(new_permissions[orcid]).value
        new_role = models.SubmissionRole(
            submission_id=submission.id, user_orcid=orcid, role=role_value
        )
        db.add(new_role)
    db.commit()
