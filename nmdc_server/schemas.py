from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from nmdc_server import models


# The order in the this union is significant... it will coerce
# valid datetime strings into datetime objects while falling
# back to ordinary strings.  Also, we never want numeric types
# to be interpreted as dates.
AnnotationValue = Union[float, int, datetime, str]


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
    label: str
    url: str
    data: Dict[str, Any]

    class Config:
        orm_mode = True


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
    reads_qc: TableSummary
    metagenome_assembly: TableSummary
    metagenome_annotation: TableSummary
    metaproteomic_analysis: TableSummary


# study
class StudyBase(AnnotatedBase):
    principal_investigator_websites: List[str] = []
    publication_dois: List[str] = []
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
    has_outputs: List[str]

    class Config:
        orm_mode = True


# biosample
class BiosampleBase(AnnotatedBase):
    project_id: str
    depth: Optional[float]
    env_broad_scale_id: Optional[str]
    env_local_scale_id: Optional[str]
    env_medium_id: Optional[str]
    # https://github.com/samuelcolvin/pydantic/issues/156
    longitude: float = Field(..., gt=-180, le=180)
    latitude: float = Field(..., ge=-90, le=90)
    add_date: datetime
    mod_date: datetime


class BiosampleCreate(BiosampleBase):
    pass


class Biosample(BiosampleBase):
    open_in_gold: str
    env_broad_scale: Optional[EnvoTerm]
    env_local_scale: Optional[EnvoTerm]
    env_medium: Optional[EnvoTerm]
    env_broad_scale_terms: List[str]
    env_local_scale_terms: List[str]
    env_medium_terms: List[str]

    class Config:
        orm_mode = True


# data_object
class DataObjectBase(BaseModel):
    id: str
    name: str
    description: str = ""
    file_size_bytes: int
    md5_checksum: Optional[str]


class DataObjectCreate(DataObjectBase):
    pass


class DataObject(DataObjectBase):
    class Config:
        orm_mode = True


class PipelineStepBase(BaseModel):
    id: str
    name: str
    type: str
    git_url: str
    started_at_time: datetime
    ended_at_time: datetime
    execution_resource: str
    project_id: str
    stats: Dict[str, Union[int, float]]


class PipelineStep(PipelineStepBase):
    has_inputs: List[str]
    has_outputs: List[str]

    class Config:
        orm_mode = True


class ReadsQCBase(PipelineStepBase):
    input_read_count: int
    input_read_bases: int
    output_read_count: int
    output_read_bases: int


class ReadsQC(PipelineStep):
    pass


class MetagenomeAssemblyBase(PipelineStepBase):
    scaffolds: int
    contigs: int
    scaf_bp: int
    contig_bp: int
    scaf_N50: int
    scaf_L50: int
    ctg_N50: int
    ctg_L50: int
    scaf_N90: int
    scaf_L90: int
    ctg_N90: int
    ctg_L90: int
    scaf_max: int
    ctg_max: int
    scaf_n_gt50K: int
    scaf_l_gt50k: int
    scaf_pct_gt50K: int
    num_input_reads: int
    num_aligned_reads: int
    scaf_logsum: float
    scaf_powsum: float
    ctg_logsum: float
    ctg_powsum: float
    asm_score: float
    gap_pct: float
    gc_avg: float
    gc_std: float


class MetagenomeAssembly(PipelineStep):
    pass


class MetagenomeAnnotationBase(PipelineStepBase):
    pass


class MetagenomeAnnotation(PipelineStep):
    pass


class MetaproteomicAnalysisBase(PipelineStepBase):
    pass


class MetaproteomicAnalysis(PipelineStep):
    pass
