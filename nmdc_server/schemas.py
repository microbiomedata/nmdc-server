"""
This module contains pydantic schemas for data serialization.

The schemas defined here are for simple CRUD methods on domain objects.
Additional schemas exist in other modules for more specialized use cases.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote
from uuid import UUID

from pint import Unit
from pydantic import BaseModel, Field, validator
from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, LargeBinary, String
from sqlalchemy.dialects.postgresql.json import JSONB

from nmdc_server import models
from nmdc_server.data_object_filters import DataObjectFilter, WorkflowActivityTypeEnum

DateType = Union[datetime, date]

# The order in the this union is significant... it will coerce
# valid datetime strings into datetime objects while falling
# back to ordinary strings.  Also, we never want numeric types
# to be interpreted as dates.
AnnotationValue = Union[float, int, datetime, str, dict, list, None]


class ErrorSchema(BaseModel):
    message: str = Field(
        ...,
        description="Human-readable error message.",
        example="Something went wrong.",
    )


class InternalErrorSchema(ErrorSchema):
    exception_id: str = Field(
        ...,
        description="Unique identifier for the error that occurred. Provide this to system "
        "administrators if you are reporting an error.",
        example="dd4c4fa3-8d22-4768-8b0d-0923140d9f8a",
    )


class AttributeType(Enum):
    string = "string"
    integer = "integer"
    float_ = "float"
    date = "date"

    @classmethod
    def from_column(cls, column: Column) -> "AttributeType":
        if isinstance(column.type, DateTime):
            return AttributeType.date
        elif isinstance(column.type, Float):
            return AttributeType.float_
        elif isinstance(column.type, (BigInteger, Integer)):
            return AttributeType.integer
        elif isinstance(column.type, String):
            return AttributeType.string
        elif isinstance(column.type, JSONB):
            raise ValueError("Cannot summarize JSONB")
        elif isinstance(column.type, LargeBinary):
            raise ValueError("Cannot summarize LargeBinary")

        raise Exception("Unknown column type")


class EnvoTerm(BaseModel):
    id: str
    label: str
    url: str
    data: Dict[str, Any]

    class Config:
        orm_mode = True


class AnnotatedBase(BaseModel):
    id: str
    name: str = ""
    description: str = ""
    alternate_identifiers: List[str] = []
    annotations: Dict[str, AnnotationValue] = {}


# aggregations
class UnitDimensionality(BaseModel):
    quantity: str
    exponent: int


class UnitInfo(BaseModel):
    name: str
    abbreviation: str
    dimensionality: List[UnitDimensionality]

    @classmethod
    def from_unit(cls, unit: Optional[Unit]) -> Optional["UnitInfo"]:
        if unit is None:
            return None

        dimensionality: List[UnitDimensionality] = []

        for key, value in unit.dimensionality.items():
            dimensionality.append(
                UnitDimensionality(
                    quantity=key,
                    exponent=value,
                )
            )

        return UnitInfo(
            name=str(unit),
            abbreviation=format(unit, "~"),
            dimensionality=dimensionality,
        )


class AttributeSummary(BaseModel):
    count: int
    min: Optional[Union[float, datetime]]
    max: Optional[Union[float, datetime]]
    type: AttributeType
    units: Optional[UnitInfo]


class TableSummary(BaseModel):
    attributes: Dict[str, AttributeSummary]
    total: int


class DatabaseSummary(BaseModel):
    study: TableSummary
    omics_processing: TableSummary
    biosample: TableSummary
    data_object: TableSummary
    reads_qc: TableSummary
    metagenome_assembly: TableSummary
    metagenome_annotation: TableSummary
    metatranscriptome_assembly: TableSummary
    metatranscriptome_annotation: TableSummary
    metaproteomic_analysis: TableSummary
    mags_analysis: TableSummary
    read_based_analysis: TableSummary
    nom_analysis: TableSummary
    metabolomics_analysis: TableSummary
    gene_function: TableSummary


class AggregationSummary(BaseModel):
    studies: int
    locations: int
    habitats: int
    data_size: int
    metagenomes: int
    metatranscriptomes: int
    proteomics: int
    metabolomics: int
    lipodomics: int
    organic_matter_characterization: int


class EnvironmentSankeyAggregation(BaseModel):
    count: int
    ecosystem: Optional[str]
    ecosystem_category: Optional[str]
    ecosystem_type: Optional[str]
    ecosystem_subtype: Optional[str]
    specific_ecosystem: Optional[str]

    class Config:
        orm_mode = True


class EnvironmentGeospatialAggregation(BaseModel):
    count: int
    latitude: Optional[float]
    longitude: Optional[float]
    ecosystem: Optional[str]
    ecosystem_category: Optional[str]

    class Config:
        orm_mode = True


class DataObjectAggregationElement(BaseModel):
    count: int = 0
    file_types: Dict[str, int] = {}


DataObjectAggregation = Dict[str, DataObjectAggregationElement]


class OrcidPerson(BaseModel):
    """https://microbiomedata.github.io/nmdc-schema/PersonValue/"""

    name: Optional[str]
    email: Optional[str]
    orcid: Optional[str]
    profile_image_url: Optional[str]

    class Config:
        orm_mode = True


class CreditAssociation(BaseModel):
    """https://microbiomedata.github.io/nmdc-schema/CreditAssociation/"""

    applied_roles: List[str]
    applies_to_person: OrcidPerson


class DOIInfo(BaseModel):
    id: str
    info: dict
    doi_category: models.DOIType
    doi_provider: str

    class Config:
        orm_mode = True


class StudyBase(AnnotatedBase):
    principal_investigator_websites: Optional[List[str]] = []
    gold_name: str = ""
    gold_description: str = ""
    scientific_objective: str = ""
    add_date: Optional[DateType]
    mod_date: Optional[DateType]
    has_credit_associations: Optional[List[CreditAssociation]]
    relevant_protocols: Optional[List[str]]
    funding_sources: Optional[List[str]]
    gold_study_identifiers: Optional[List[str]]
    homepage_website: Optional[List[str]]
    part_of: Optional[List[str]]
    study_category: Optional[str]
    children: Optional[List[Study]] = []

    @validator("principal_investigator_websites", pre=True, each_item=True)
    def replace_websites(cls, study_website: Union[models.StudyWebsite, str]) -> str:
        if isinstance(study_website, str):
            return study_website
        return study_website.website.url


class StudyCreate(StudyBase):
    principal_investigator_id: Optional[UUID]
    image: Optional[bytes]


class OmicsCounts(BaseModel):
    type: str
    count: int

    @validator("count", pre=True, always=True)
    def insert_zero(cls, v):
        return v or 0


class Study(StudyBase):
    open_in_gold: Optional[str]
    principal_investigator: Optional[OrcidPerson]
    principal_investigator_name: Optional[str]
    image_url: str
    principal_investigator_image_url: str
    sample_count: Optional[int]
    omics_counts: Optional[List[OmicsCounts]]
    omics_processing_counts: Optional[List[OmicsCounts]]
    doi_map: Dict[str, Any] = {}
    multiomics: int

    class Config:
        orm_mode = True


# biosample
class BiosampleBase(AnnotatedBase):
    study_id: str
    depth: Optional[float]
    env_broad_scale_id: Optional[str]
    env_local_scale_id: Optional[str]
    env_medium_id: Optional[str]
    # https://github.com/samuelcolvin/pydantic/issues/156
    longitude: Optional[float] = Field(default=None, gt=-180, le=180)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    add_date: Optional[DateType]
    mod_date: Optional[DateType]

    collection_date: Optional[DateType]
    ecosystem: Optional[str]
    ecosystem_category: Optional[str]
    ecosystem_type: Optional[str]
    ecosystem_subtype: Optional[str]
    specific_ecosystem: Optional[str]

    class Config:
        orm_mode = True


class BiosampleCreate(BiosampleBase):
    emsl_biosample_identifiers: List[str] = []


class Biosample(BiosampleBase):
    open_in_gold: Optional[str]
    env_broad_scale: Optional[EnvoTerm]
    env_local_scale: Optional[EnvoTerm]
    env_medium: Optional[EnvoTerm]
    env_broad_scale_terms: List[str] = []
    env_local_scale_terms: List[str] = []
    env_medium_terms: List[str] = []
    emsl_biosample_identifiers: Optional[List[str]]

    omics_processing: List["OmicsProcessing"]
    multiomics: int

    class Config:
        orm_mode = True


# omics_processing
class OmicsProcessingBase(AnnotatedBase):
    study_id: Optional[str]
    biosample_inputs: list[BiosampleBase] = []
    add_date: Optional[DateType]
    mod_date: Optional[DateType]


class OmicsProcessingCreate(OmicsProcessingBase):
    pass


class OmicsProcessing(OmicsProcessingBase):
    open_in_gold: Optional[str]
    biosample_ids: list[str] = []

    omics_data: List["OmicsTypes"]
    outputs: List["DataObject"]

    @validator("biosample_ids")
    @classmethod
    def set_biosample_ids(cls, biosample_ids: list[str], values: dict[str, Any]) -> list[str]:
        # Only capture biosample IDs in responses
        biosample_objects: list[BiosampleBase] = values.get("biosample_inputs", [])
        biosample_ids = biosample_ids + [biosample.id for biosample in biosample_objects]
        values.pop("biosample_inputs")

        return biosample_ids

    class Config:
        orm_mode = True


# data_object
class DataObjectBase(BaseModel):
    id: str
    name: str
    description: str = ""
    file_size_bytes: Optional[int]
    md5_checksum: Optional[str]
    url: Optional[str]
    downloads: int
    file_type: Optional[str] = None
    file_type_description: Optional[str] = None


class DataObjectCreate(DataObjectBase):
    pass


class DataObject(DataObjectBase):
    selected: Optional[bool] = None

    class Config:
        orm_mode = True

    @validator("url")
    def replace_url(cls, url, values):
        id_str = quote(values["id"])
        return f"/api/data_object/{id_str}/download" if url else None

    # Determine if the data object is selected by the provided filter.
    # WARNING: This logic is duplicated in the bulk download query
    #          (see `_data_object_filter_subquery`)
    @classmethod
    def is_selected(
        cls,
        workflow: WorkflowActivityTypeEnum,
        data_object: "DataObject",
        filters: List[DataObjectFilter],
    ) -> bool:
        # we can't download files without urls
        if not data_object.url:
            return False

        def workflow_match(f, workflow) -> bool:
            if f.workflow is None or f.workflow == workflow:
                return True
            return False

        def file_type_match(f, file_type) -> bool:
            if f.file_type is None or f.file_type == file_type:
                return True
            return False

        for f in filters:
            if workflow_match(f, workflow) and file_type_match(f, data_object.file_type):
                return True

        return False


class GeneFunction(BaseModel):
    class Config:
        orm_mode = True

    id: str


class PipelineStepBase(BaseModel):
    id: str
    name: str = ""
    type: str
    git_url: str
    started_at_time: DateType
    ended_at_time: DateType
    execution_resource: str
    omics_processing_id: str


class PipelineStep(PipelineStepBase):
    # has_inputs: List[str]
    # has_outputs: List[str]
    outputs: List[DataObject]

    class Config:
        orm_mode = True


class ReadsQCBase(PipelineStepBase):
    type: str = WorkflowActivityTypeEnum.reads_qc.value
    input_read_count: Optional[int]
    input_read_bases: Optional[int]
    output_read_count: Optional[int]
    output_read_bases: Optional[int]


class ReadsQC(PipelineStep):
    pass


class AssemblyBase(PipelineStepBase):
    scaffolds: Optional[int]
    contigs: Optional[int]
    scaf_bp: Optional[int]
    contig_bp: Optional[int]
    scaf_n50: Optional[int]
    scaf_l50: Optional[int]
    ctg_n50: Optional[int]
    ctg_l50: Optional[int]
    scaf_n90: Optional[int]
    scaf_l90: Optional[int]
    ctg_n90: Optional[int]
    ctg_l90: Optional[int]
    scaf_max: Optional[int]
    ctg_max: Optional[int]
    scaf_n_gt50k: Optional[int]

    # TODO: fix the data on ingest or make this optional on the schema
    scaf_l_gt50k: Optional[int]
    scaf_pct_gt50k: Optional[int]
    num_input_reads: Optional[int]
    num_aligned_reads: Optional[int]
    scaf_logsum: Optional[float]
    scaf_powsum: Optional[float]
    ctg_logsum: Optional[float]
    ctg_powsum: Optional[float]
    asm_score: Optional[float]
    gap_pct: Optional[float]
    gc_avg: Optional[float]
    gc_std: Optional[float]


class MetagenomeAssemblyBase(AssemblyBase):
    type: str = WorkflowActivityTypeEnum.metagenome_assembly.value


class MetatranscriptomeAssemblyBase(AssemblyBase):
    type: str = WorkflowActivityTypeEnum.metatranscriptome_assembly.value


class MetagenomeAssembly(PipelineStep):
    pass


class MetatranscriptomeAssembly(PipelineStep):
    pass


class MetagenomeAnnotationBase(PipelineStepBase):
    type: str = WorkflowActivityTypeEnum.metagenome_annotation.value


class MetatranscriptomeAnnotationBase(PipelineStepBase):
    type: str = WorkflowActivityTypeEnum.metatranscriptome_annotation.value


class MetagenomeAnnotation(PipelineStep):
    pass


class MetatranscriptomeAnnotation(PipelineStep):
    pass


class MetaproteomicAnalysisBase(PipelineStepBase):
    type: str = WorkflowActivityTypeEnum.metaproteomic_analysis.value


class MetaproteomicAnalysis(PipelineStep):
    pass


class MAG(BaseModel):
    bin_name: Optional[str]
    number_of_contig: Optional[int]
    completeness: Optional[float]
    contamination: Optional[float]
    gene_count: Optional[int]
    bin_quality: Optional[str]
    num_16s: Optional[int]
    num_5s: Optional[int]
    num_23s: Optional[int]
    num_t_rna: Optional[int]


class MAGCreate(MAG):
    mags_analysis: "MAGsAnalysis"


class MAGsAnalysisBase(PipelineStepBase):
    type: str = WorkflowActivityTypeEnum.mags_analysis.value
    input_contig_num: Optional[int]
    too_short_contig_num: Optional[int]
    low_depth_contig_num: Optional[int]
    unbinned_contig_num: Optional[int]
    binned_contig_num: Optional[int]


class MAGsAnalysis(PipelineStep):
    type: str = WorkflowActivityTypeEnum.mags_analysis.value
    input_contig_num: Optional[int]
    too_short_contig_num: Optional[int]
    low_depth_contig_num: Optional[int]
    unbinned_contig_num: Optional[int]
    binned_contig_num: Optional[int]

    mags_list: List[MAG]


class NOMAnalysisBase(PipelineStepBase):
    type: str = WorkflowActivityTypeEnum.nom_analysis.value
    used: str


class NOMAnalysis(PipelineStep):
    pass


class ReadBasedAnalysisBase(PipelineStepBase):
    type: str = WorkflowActivityTypeEnum.read_based_analysis.value


class ReadBasedAnalysis(PipelineStep):
    pass


class MetatranscriptomeBase(PipelineStepBase):
    type: str = WorkflowActivityTypeEnum.metatranscriptome.value


class Metatranscriptome(PipelineStep):
    pass


class MetabolomicsAnalysisBase(PipelineStepBase):
    type: str = WorkflowActivityTypeEnum.metabolomics_analysis.value
    used: str
    has_calibration: str


class MetabolomicsAnalysis(PipelineStep):
    pass


OmicsTypes = Union[
    ReadsQC,
    MetagenomeAnnotation,
    MetagenomeAssembly,
    MetatranscriptomeAnnotation,
    MetatranscriptomeAssembly,
    MetaproteomicAnalysis,
    MAGsAnalysis,
    NOMAnalysis,
    ReadBasedAnalysis,
    MetabolomicsAnalysis,
    Metatranscriptome,
]
OmicsProcessing.update_forward_refs()
Biosample.update_forward_refs()
MAGCreate.update_forward_refs()


class FileDownloadMetadata(BaseModel):
    ip: str
    user_agent: str
    orcid: str


class FileDownloadBase(FileDownloadMetadata):
    ip: str
    user_agent: str
    orcid: str
    data_object_id: str


class FileDownload(FileDownloadBase):
    id: str
    created: DateType


class FileDownloadCreate(FileDownloadBase):
    pass


class EnvoTreeNode(BaseModel):
    id: str
    label: str
    children: List[EnvoTreeNode]


EnvoTreeNode.update_forward_refs()


class EnvoTreeResponse(BaseModel):
    trees: Dict[str, List[EnvoTreeNode]]


class KeggTermListResponse(BaseModel):
    terms: List[str]


class KeggTermText(BaseModel):
    term: str
    text: str

    class Config:
        orm_mode = True


class KeggTermTextListResponse(BaseModel):
    terms: List[KeggTermText]


class IngestArgumentSchema(BaseModel):
    skip_annotation: bool = False
    function_limit: int = 0  # Default to no limit


class User(BaseModel):
    id: Optional[UUID]
    orcid: str
    name: str = ""
    is_admin = False

    class Config:
        orm_mode = True


class LockOperationResult(BaseModel):
    success: bool
    message: str
    locked_by: Optional[User]
    lock_updated: Optional[datetime]
