from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from nmdc_server import models


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


class EnvoTerm(BaseModel):
    id: str
    data: Dict[str, Any]


class AnnotatedBase(BaseModel):
    id: str
    name: str
    description: str = ""
    alternate_identifiers: List[str] = []
    annotations: Dict[str, AnnotationValue] = {}


# summary
class TableSummary(BaseModel):
    attributes: Dict[str, int]
    total: int


class DatabaseSummary(BaseModel):
    study: TableSummary
    project: TableSummary
    biosample: TableSummary
    data_object: TableSummary


# study
class StudyBase(AnnotatedBase):
    principal_investigator_websites: List[str] = Field(default_factory=list)
    publication_dois: List[str] = Field(default_factory=list)
    gold_name: str = ""
    gold_description: str = ""
    scientific_objective: str = ""
    add_date: datetime
    mod_date: datetime

    @validator("principal_investigator_websites", pre=True, each_item=True)
    def replace_websites(cls, study_website: Union[models.StudyWebsite, str]) -> str:
        if isinstance(study_website, str):
            return study_website
        return study_website.website.url

    @validator("publication_dois", pre=True, each_item=True)
    def replace_dois(cls, study_publication: Union[models.StudyPublication, str]) -> str:
        if isinstance(study_publication, str):
            return study_publication
        return study_publication.publication.doi


class StudyCreate(StudyBase):
    pass


class Study(StudyBase):
    open_in_gold: str

    class Config:
        orm_mode = True


# project
class ProjectBase(AnnotatedBase):
    study_id: str
    add_date: datetime
    mod_date: datetime


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    study_id: str
    open_in_gold: str

    class Config:
        orm_mode = True


# biosample
class BiosampleBase(AnnotatedBase):
    project_id: str
    depth: Optional[float]
    env_broad_scale: str
    env_local_scale: str
    env_medium: str
    # https://github.com/samuelcolvin/pydantic/issues/156
    longitude: float = Field(..., gt=-180, le=180)
    latitude: float = Field(..., ge=-90, le=90)
    add_date: datetime
    mod_date: datetime


class BiosampleCreate(BiosampleBase):
    pass


class Biosample(BiosampleBase):
    open_in_gold: str

    class Config:
        orm_mode = True


# data_object
class DataObjectBase(AnnotatedBase):
    project_id: str
    file_size_bytes: int


class DataObjectCreate(DataObjectBase):
    pass


class DataObject(DataObjectBase):
    project: Project

    class Config:
        orm_mode = True
