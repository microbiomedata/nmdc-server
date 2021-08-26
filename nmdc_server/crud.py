from logging import getLogger
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, cast
from uuid import UUID

from sqlalchemy.orm import Query, Session

from nmdc_server import aggregations, bulk_download_schema, models, query, schemas
from nmdc_server.data_object_filters import get_local_data_url

logger = getLogger(__name__)
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
    return (
        db.query(models.SearchIndex)
        .filter(models.SearchIndex.value.ilike(searchtext))
        .limit(limit)
        .all()
    )


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


def create_study(db: Session, study: schemas.StudyCreate) -> models.Study:
    study_dict = study.dict()

    websites = study_dict.pop("principal_investigator_websites")
    publications = study_dict.pop("publication_dois")

    db_study = models.Study(**study_dict)

    for url in websites:
        website, _ = get_or_create(db, models.Website, url=url)
        study_website = models.StudyWebsite(website=website)
        db_study.principal_investigator_websites.append(study_website)  # type: ignore

    for doi in publications:
        publication, _ = get_or_create(db, models.Publication, doi=doi)
        study_publication = models.StudyPublication(publication=publication)
        db_study.publication_dois.append(study_publication)  # type: ignore

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
    biosample = cast(Optional[models.Biosample], omics_processing.biosample)

    def safe_name(name: str) -> str:
        return name.replace("/", "_").replace("\\", "_").replace(":", "_")

    op_name = safe_name(omics_processing.id)

    if biosample is not None:
        biosample_name = safe_name(biosample.id)
        study = biosample.study
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

        # TODO: Support arbitrary urls
        if data_object.url is None or not data_object.url.startswith(
            "https://data.microbiomedata.org/data"
        ):
            if data_object and data_object.url is None:
                logger.warning("Data object url is empty")
            if data_object and data_object.url is not None:
                logger.warning(f"Data object url is {data_object.url}")
            continue

        url = get_local_data_url(data_object.url)
        if url is None:
            logger.warning("Unknown host in data url")
            continue

        # TODO: add crc checksums to support retries
        # TODO: add directory structure and metadata
        content.append(f"- {data_object.file_size_bytes} {url} {file.path}")

    return "\n".join(content) + "\n"
