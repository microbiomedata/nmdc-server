from datetime import datetime
from typing import Dict, Union

from pydantic import BaseModel, Field


# The order in the this union is significant... it will coerce
# valid datetime strings into datetime objects while falling
# back to ordinary strings.  Also, we never want numeric types
# to be interpreted as dates.
AnnotationValue = Union[int, float, datetime, str]


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


class AnnotatedBase(BaseModel):
    id: str
    name: str
    description: str = ""
    annotations: Dict[str, AnnotationValue] = {}


# study
class StudyBase(AnnotatedBase):
    pass


class StudyCreate(StudyBase):
    pass


class Study(StudyBase):
    class Config:
        orm_mode = True


# project
class ProjectBase(AnnotatedBase):
    pass


class ProjectCreate(ProjectBase):
    study_id: str


class Project(ProjectBase):
    study: Study

    class Config:
        orm_mode = True


# biosample
class BiosampleBase(AnnotatedBase):
    # https://github.com/samuelcolvin/pydantic/issues/156
    longitude: float = Field(..., gt=-180, le=180)
    latitude: float = Field(..., ge=-90, le=90)


class BiosampleCreate(BiosampleBase):
    project_id: str


class Biosample(BiosampleBase):
    project: Project

    class Config:
        orm_mode = True


# data_object
class DataObjectBase(AnnotatedBase):
    pass


class DataObjectCreate(DataObjectBase):
    project_id: str


class DataObject(DataObjectBase):
    project: Project

    class Config:
        orm_mode = True
