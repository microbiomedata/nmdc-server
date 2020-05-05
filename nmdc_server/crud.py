from typing import List, Optional

from sqlalchemy.orm import Session

from nmdc_server import models, query, schemas


# study
def get_study(db: Session, study_id: str) -> Optional[models.Study]:
    return db.query(models.Study).filter(models.Study.id == study_id).first()


def create_study(db: Session, study: schemas.StudyCreate) -> models.Study:
    db_study = models.Study(**study.dict())
    db.add(db_study)
    db.commit()
    db.refresh(db_study)
    return db_study


def delete_study(db: Session, study: models.Study) -> None:
    db.delete(study)
    db.commit()


def search_study(db: Session, conditions: List[query.ConditionSchema]) -> List[models.Study]:
    return list(query.StudyQuerySchema(conditions=conditions).execute(db))


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


def search_project(db: Session, conditions: List[query.ConditionSchema]) -> List[models.Project]:
    return list(query.ProjectQuerySchema(conditions=conditions).execute(db))


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


def search_biosample(
    db: Session, conditions: List[query.ConditionSchema]
) -> List[models.Biosample]:
    return list(query.BiosampleQuerySchema(conditions=conditions).execute(db))


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


def search_data_object(
    db: Session, conditions: List[query.ConditionSchema]
) -> List[models.DataObject]:
    return list(query.DataObjectQuerySchema(conditions=conditions).execute(db))


def facet_data_object(
    db: Session, attribute: str, conditions: List[query.ConditionSchema]
) -> query.FacetResponse:
    facets = query.DataObjectQuerySchema(conditions=conditions).facet(db, attribute)
    return query.FacetResponse(facets=facets)
