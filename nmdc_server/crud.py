from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar

from sqlalchemy import func
from sqlalchemy.orm import Query, Session

from nmdc_server import models, query, schemas

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


# summary
def get_table_summary(db: Session, model: models.ModelType) -> schemas.TableSummary:
    count = db.query(model).count()
    attribute = func.jsonb_object_keys(model.annotations)
    q = db.query(attribute, func.count()).group_by(attribute)

    attributes = {row[0]: row[1] for row in q}
    for column in model.__table__.columns:
        if column.name not in ["annotations", "alternate_identifiers"] and "_id" not in column.name:
            attributes[column.name] = count

    if model == models.Biosample:
        attributes["env_medium"] = count
        attributes["env_local_scale"] = count
        attributes["env_broad_scale"] = count

    return schemas.TableSummary(total=count, attributes=attributes)


def get_database_summary(db: Session) -> schemas.DatabaseSummary:
    return schemas.DatabaseSummary(
        study=get_table_summary(db, models.Study),
        project=get_table_summary(db, models.Project),
        biosample=get_table_summary(db, models.Biosample),
        data_object=get_table_summary(db, models.DataObject),
    )


# study
def get_study(db: Session, study_id: str) -> Optional[models.Study]:
    return db.query(models.Study).filter(models.Study.id == study_id).first()


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
    db: Session, attribute: str, conditions: List[query.ConditionSchema]
) -> query.FacetResponse:
    facets = query.BiosampleQuerySchema(conditions=conditions).facet(db, attribute)
    return query.FacetResponse(facets=facets)


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


def search_data_object(db: Session, conditions: List[query.ConditionSchema]) -> Query:
    return query.DataObjectQuerySchema(conditions=conditions).execute(db)


def facet_data_object(
    db: Session, attribute: str, conditions: List[query.ConditionSchema]
) -> query.FacetResponse:
    facets = query.DataObjectQuerySchema(conditions=conditions).facet(db, attribute)
    return query.FacetResponse(facets=facets)
