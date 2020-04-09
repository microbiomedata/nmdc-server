from typing import Optional

from sqlalchemy.orm import Session

from . import models


def get_study(db: Session, study_id: str) -> Optional[models.Study]:
    return db.query(models.Study).filter(models.Study.id == study_id).first()


def get_project(db: Session, project_id: str) -> Optional[models.Project]:
    return db.query(models.Project).filter(models.Project.id == project_id).first()


def get_biosample(db: Session, biosample_id: str) -> Optional[models.Biosample]:
    return db.query(models.Biosample).filter(models.Biosample.id == biosample_id).first()


def get_data_object(db: Session, data_object_id: str) -> Optional[models.DataObject]:
    return db.query(models.DataObject).filter(models.DataObject.id == data_object_id).first()
