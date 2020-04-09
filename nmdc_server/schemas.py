from datetime import datetime
from typing import Dict, Union

from pydantic import BaseModel, Field

AnnotationValue = Union[int, float, str, datetime]


class ErrorSchema(BaseModel):
    message: str = Field(
        ..., description="Human-readable error message.", example="Something went wrong.",
    )


class InternalErrorSchema(ErrorSchema):
    exception_id: str = Field(
        ...,
        description="Unique identifier for the error that occurred. Provide this to system "
        "administrators if you are reporting an error.",
        example="dd4c4fa3-8d22-4768-8b0d-0923140d9f8a",
    )


class SearchResponse(BaseModel):
    pass


class SearchQuery(BaseModel):
    pass


class AnnotatedBase(BaseModel):
    id: str
    name: str
    description: str = ""
    annotations: Dict[str, AnnotationValue] = {}


class StudyBase(AnnotatedBase):
    pass


class StudyCreate(StudyBase):
    pass


class Study(StudyBase):
    class Config:
        orm_mode = True


class ProjectBase(AnnotatedBase):
    pass


class ProjectCreate(ProjectBase):
    study_id: str


class Project(ProjectBase):
    study: Study

    class Config:
        orm_mode = True


class BiosampleBase(AnnotatedBase):
    pass


class BiosampleCreate(BiosampleBase):
    project_id: str


class Biosample(BiosampleBase):
    project: Project

    class Config:
        orm_mode = True


class DataObjectBase(AnnotatedBase):
    pass


class DataObjectCreate(DataObjectBase):
    project_id: str


class DataObject(DataObjectBase):
    project: Project

    class Config:
        orm_mode = True
