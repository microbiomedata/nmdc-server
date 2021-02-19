from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar
from uuid import UUID

from sqlalchemy.orm import Query, Session

from nmdc_server import aggregations, models, query, schemas

NumericValue = query.NumericValue
T = TypeVar("T", bound=models.Base)


# See: https://docs.djangoproject.com/en/3.0/ref/models/querysets/#get-or-create
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
        project=aggregations.get_table_summary(db, models.Project),
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
        gene_function=gene_function,
    )


def get_aggregated_stats(db: Session) -> schemas.AggregationSummary:
    return aggregations.get_aggregation_summary(db)


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


# project
def get_project(db: Session, project_id: str) -> Optional[models.Project]:
    return db.query(models.Project).filter(models.Project.id == project_id).first()


def create_project(db: Session, project: schemas.ProjectCreate) -> models.Project:
    db_project = models.Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def delete_project(db: Session, project: models.Project) -> None:
    db.delete(project)
    db.commit()


def search_project(db: Session, conditions: List[query.ConditionSchema]) -> Query:
    return query.ProjectQuerySchema(conditions=conditions).execute(db)


def facet_project(
    db: Session, attribute: str, conditions: List[query.ConditionSchema]
) -> query.FacetResponse:
    facets = query.ProjectQuerySchema(conditions=conditions).facet(db, attribute)
    return query.FacetResponse(facets=facets)


def binned_facet_project(
    db: Session,
    attribute: str,
    conditions: List[query.ConditionSchema],
    **kwargs,
) -> query.BinnedFacetResponse:
    bins, facets = query.ProjectQuerySchema(conditions=conditions).binned_facet(
        db, attribute, **kwargs
    )
    return query.BinnedFacetResponse(bins=bins, facets=facets)


def list_project_data_objects(db: Session, id: str) -> Query:
    return (
        db.query(models.DataObject)
        .join(models.project_output_association)
        .filter(models.project_output_association.c.project_id == id)
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


def search_biosample(db: Session, conditions: List[query.ConditionSchema]) -> Query:
    return query.BiosampleQuerySchema(conditions=conditions).execute(db)


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


# readsqc
def get_reads_qc(db: Session, reads_qc_id: str) -> Optional[models.ReadsQC]:
    return db.query(models.ReadsQC).filter(models.ReadsQC.id == reads_qc_id).first()


def search_reads_qc(db: Session, conditions: List[query.ConditionSchema]) -> Query:
    return query.ReadsQCQuerySchema(conditions=conditions).execute(db)


def facet_reads_qc(
    db: Session, attribute: str, conditions: List[query.ConditionSchema]
) -> query.FacetResponse:
    facets = query.ReadsQCQuerySchema(conditions=conditions).facet(db, attribute)
    return query.FacetResponse(facets=facets)


def binned_facet_reads_qc(
    db: Session,
    attribute: str,
    conditions: List[query.ConditionSchema],
    **kwargs,
) -> query.BinnedFacetResponse:
    bins, facets = query.ReadsQCQuerySchema(conditions=conditions).binned_facet(
        db, attribute, **kwargs
    )
    return query.BinnedFacetResponse(bins=bins, facets=facets)


def list_reads_qc_data_objects(db: Session, id: str) -> Query:
    return (
        db.query(models.DataObject)
        .join(models.reads_qc_output_association)
        .filter(models.reads_qc_output_association.c.reads_qc_id == id)
    )


# metagenome assembly
def get_metagenome_assembly(
    db: Session, metagenome_assembly_id: str
) -> Optional[models.MetagenomeAssembly]:
    return (
        db.query(models.MetagenomeAssembly)
        .filter(models.MetagenomeAssembly.id == metagenome_assembly_id)
        .first()
    )


def search_metagenome_assembly(db: Session, conditions: List[query.ConditionSchema]) -> Query:
    return query.MetagenomeAssemblyQuerySchema(conditions=conditions).execute(db)


def facet_metagenome_assembly(
    db: Session, attribute: str, conditions: List[query.ConditionSchema]
) -> query.FacetResponse:
    facets = query.MetagenomeAssemblyQuerySchema(conditions=conditions).facet(db, attribute)
    return query.FacetResponse(facets=facets)


def binned_facet_metagenome_assembly(
    db: Session,
    attribute: str,
    conditions: List[query.ConditionSchema],
    **kwargs,
) -> query.BinnedFacetResponse:
    bins, facets = query.MetagenomeAssemblyQuerySchema(conditions=conditions).binned_facet(
        db, attribute, **kwargs
    )
    return query.BinnedFacetResponse(bins=bins, facets=facets)


def list_metagenome_assembly_data_objects(db: Session, id: str) -> Query:
    return (
        db.query(models.DataObject)
        .join(models.metagenome_assembly_output_association)
        .filter(models.metagenome_assembly_output_association.c.metagenome_assembly_id == id)
    )


# metagenome annotation
def get_metagenome_annotation(
    db: Session, metagenome_annotation_id: str
) -> Optional[models.MetagenomeAnnotation]:
    return (
        db.query(models.MetagenomeAnnotation)
        .filter(models.MetagenomeAnnotation.id == metagenome_annotation_id)
        .first()
    )


def search_metagenome_annotation(db: Session, conditions: List[query.ConditionSchema]) -> Query:
    return query.MetagenomeAnnotationQuerySchema(conditions=conditions).execute(db)


def facet_metagenome_annotation(
    db: Session, attribute: str, conditions: List[query.ConditionSchema]
) -> query.FacetResponse:
    facets = query.MetagenomeAnnotationQuerySchema(conditions=conditions).facet(db, attribute)
    return query.FacetResponse(facets=facets)


def binned_facet_metagenome_annotation(
    db: Session,
    attribute: str,
    conditions: List[query.ConditionSchema],
    **kwargs,
) -> query.BinnedFacetResponse:
    bins, facets = query.MetagenomeAnnotationQuerySchema(conditions=conditions).binned_facet(
        db, attribute, **kwargs
    )
    return query.BinnedFacetResponse(bins=bins, facets=facets)


def list_metagenome_annotation_data_objects(db: Session, id: str) -> Query:
    return (
        db.query(models.DataObject)
        .join(models.metagenome_annotation_output_association)
        .filter(models.metagenome_annotation_output_association.c.metagenome_annotation_id == id)
    )


# metaproteomic analysis
def get_metaproteomic_analysis(
    db: Session, metaproteomic_analysis_id: str
) -> Optional[models.MetaproteomicAnalysis]:
    return (
        db.query(models.MetaproteomicAnalysis)
        .filter(models.MetaproteomicAnalysis.id == metaproteomic_analysis_id)
        .first()
    )


def search_metaproteomic_analysis(db: Session, conditions: List[query.ConditionSchema]) -> Query:
    return query.MetaproteomicAnalysisQuerySchema(conditions=conditions).execute(db)


def facet_metaproteomic_analysis(
    db: Session, attribute: str, conditions: List[query.ConditionSchema]
) -> query.FacetResponse:
    facets = query.MetaproteomicAnalysisQuerySchema(conditions=conditions).facet(db, attribute)
    return query.FacetResponse(facets=facets)


def binned_facet_metaproteomic_analysis(
    db: Session,
    attribute: str,
    conditions: List[query.ConditionSchema],
    **kwargs,
) -> query.BinnedFacetResponse:
    bins, facets = query.MetaproteomicAnalysisQuerySchema(conditions=conditions).binned_facet(
        db, attribute, **kwargs
    )
    return query.BinnedFacetResponse(bins=bins, facets=facets)


def list_metaproteomic_analysis_data_objects(db: Session, id: str) -> Query:
    return (
        db.query(models.DataObject)
        .join(models.metaproteomic_analysis_output_association)
        .filter(models.metaproteomic_analysis_output_association.c.metaproteomic_analysis_id == id)
    )


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
