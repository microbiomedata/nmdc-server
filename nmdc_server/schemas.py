"""
This module contains pydantic schemas for data serialization.

The schemas defined here are for simple CRUD methods on domain objects.
Additional schemas exist in other modules for more specialized use cases.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from importlib.metadata import version
from typing import Annotated, Any, Dict, List, Optional, Union
from urllib.parse import quote
from uuid import UUID

from pint import Unit
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, ValidationInfo, field_validator
from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, LargeBinary, String
from sqlalchemy.dialects.postgresql.json import JSONB

from nmdc_server import __version__, models
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
        examples=["Something went wrong."],
    )


class InternalErrorSchema(ErrorSchema):
    exception_id: str = Field(
        ...,
        description="Unique identifier for the error that occurred. Provide this to system "
        "administrators if you are reporting an error.",
        examples=["dd4c4fa3-8d22-4768-8b0d-0923140d9f8a"],
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
    model_config = ConfigDict(from_attributes=True)


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
    min: Optional[Union[float, datetime]] = None
    max: Optional[Union[float, datetime]] = None
    type: AttributeType
    units: Optional[UnitInfo] = None


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
    non_parent_studies: int
    locations: int
    habitats: int
    metagenomes: int
    metatranscriptomes: int
    proteomics: int
    metabolomics: int
    lipodomics: int
    organic_matter_characterization: int
    wfe_output_data_size_bytes: int
    data_size: int


class AdminStats(BaseModel):
    """Statistics designed for consumption by Data Portal/Submission Portal administrators."""

    num_user_accounts: int = Field(
        description="Number of distinct ORCIDs that have been used to sign in."
    )


class EnvironmentSankeyAggregation(BaseModel):
    count: int
    ecosystem: Optional[str] = None
    ecosystem_category: Optional[str] = None
    ecosystem_type: Optional[str] = None
    ecosystem_subtype: Optional[str] = None
    specific_ecosystem: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class EnvironmentGeospatialAggregation(BaseModel):
    count: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ecosystem: Optional[str] = None
    ecosystem_category: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class DataObjectAggregationNode(BaseModel):
    count: int = 0
    size: int = 0


class DataObjectAggregationElement(DataObjectAggregationNode):
    file_types: Dict[str, DataObjectAggregationNode] = {}


DataObjectAggregation = Dict[str, DataObjectAggregationElement]


class OrcidPerson(BaseModel):
    """https://microbiomedata.github.io/nmdc-schema/PersonValue/"""

    name: Optional[str] = None
    email: Optional[str] = None
    orcid: Optional[str] = None
    profile_image_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class CreditAssociation(BaseModel):
    """https://microbiomedata.github.io/nmdc-schema/CreditAssociation/"""

    applied_roles: List[str]
    applies_to_person: OrcidPerson


class DOIInfo(BaseModel):
    id: str
    info: dict
    doi_category: models.DOIType
    doi_provider: str
    model_config = ConfigDict(from_attributes=True)


def replace_website(site: Union[str, models.StudyWebsite]) -> str:
    if isinstance(site, models.StudyWebsite):
        return site.website.url
    return site


PiSite = Annotated[str, BeforeValidator(replace_website)]


class StudyBase(AnnotatedBase):
    principal_investigator_websites: Optional[List[PiSite]] = []
    gold_name: str = ""
    gold_description: str = ""
    scientific_objective: str = ""
    add_date: Optional[DateType] = None
    mod_date: Optional[DateType] = None
    has_credit_associations: Optional[List[CreditAssociation]] = None
    protocol_link: Optional[List[str]] = None
    funding_sources: Optional[List[str]] = None
    gold_study_identifiers: Optional[List[str]] = None
    homepage_website: Optional[List[str]] = None
    part_of: Optional[List[str]] = None
    study_category: Optional[str] = None
    children: Optional[List[Study]] = []


class StudyCreate(StudyBase):
    principal_investigator_id: Optional[UUID] = None
    image: Optional[bytes] = None


class OmicsCounts(BaseModel):
    type: str
    count: int

    @field_validator("count", mode="before")
    def insert_zero(cls, v):
        return v or 0


class Study(StudyBase):
    open_in_gold: Optional[str] = None
    principal_investigator: Optional[OrcidPerson] = None
    principal_investigator_name: Optional[str] = None
    image_url: str
    principal_investigator_image_url: str
    sample_count: Optional[int] = None
    omics_counts: Optional[List[OmicsCounts]] = None
    omics_processing_counts: Optional[List[OmicsCounts]] = None
    doi_map: Dict[str, Any] = {}
    multiomics: int
    model_config = ConfigDict(from_attributes=True)


# biosample
class BiosampleBase(AnnotatedBase):
    study_id: str
    depth: Optional[float] = None
    env_broad_scale_id: Optional[str] = None
    env_local_scale_id: Optional[str] = None
    env_medium_id: Optional[str] = None
    # https://github.com/samuelcolvin/pydantic/issues/156
    longitude: Optional[float] = Field(default=None, gt=-180, le=180)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    add_date: Optional[DateType] = None
    mod_date: Optional[DateType] = None

    collection_date: Optional[DateType] = None
    ecosystem: Optional[str] = None
    ecosystem_category: Optional[str] = None
    ecosystem_type: Optional[str] = None
    ecosystem_subtype: Optional[str] = None
    specific_ecosystem: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class BiosampleCreate(BiosampleBase):
    emsl_biosample_identifiers: List[str] = []


class Biosample(BiosampleBase):
    open_in_gold: Optional[str] = None
    env_broad_scale: Optional[EnvoTerm] = None
    env_local_scale: Optional[EnvoTerm] = None
    env_medium: Optional[EnvoTerm] = None
    env_broad_scale_terms: List[str] = []
    env_local_scale_terms: List[str] = []
    env_medium_terms: List[str] = []
    emsl_biosample_identifiers: Optional[List[str]] = None

    omics_processing: List["OmicsProcessing"]
    multiomics: int
    model_config = ConfigDict(from_attributes=True)


# omics_processing
class OmicsProcessingBase(AnnotatedBase):
    study_id: Optional[str] = None
    biosample_inputs: list[BiosampleBase] = []
    add_date: Optional[DateType] = None
    mod_date: Optional[DateType] = None


class OmicsProcessingCreate(OmicsProcessingBase):
    pass


class OmicsProcessing(OmicsProcessingBase):
    open_in_gold: Optional[str] = None
    biosample_ids: list[str] = []

    omics_data: List["OmicsTypes"]
    outputs: List["DataObject"]

    @field_validator("biosample_ids")
    @classmethod
    def set_biosample_ids(cls, biosample_ids: list[str], info: ValidationInfo) -> list[str]:
        # Only capture biosample IDs in responses
        biosample_objects: list[BiosampleBase] = info.data.get("biosample_inputs", [])
        biosample_ids = biosample_ids + [biosample.id for biosample in biosample_objects]
        info.data.pop("biosample_inputs")

        return biosample_ids

    model_config = ConfigDict(from_attributes=True)


# data_object
class DataObjectBase(BaseModel):
    id: str
    name: str
    description: str = ""
    file_size_bytes: Optional[int] = None
    md5_checksum: Optional[str] = None
    url: Optional[str] = None
    downloads: int
    file_type: Optional[str] = None
    file_type_description: Optional[str] = None


class DataObjectCreate(DataObjectBase):
    pass


class DataObject(DataObjectBase):
    selected: Optional[bool] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("url")
    def replace_url(cls, url, info: ValidationInfo):
        id_str = quote(info.data["id"])
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
    model_config = ConfigDict(from_attributes=True)

    id: str


class PipelineStepBase(BaseModel):
    id: str
    name: str = ""
    type: str
    git_url: str
    started_at_time: DateType
    ended_at_time: Optional[DateType] = None
    execution_resource: str
    omics_processing_id: str


class PipelineStep(PipelineStepBase):
    # has_inputs: List[str]
    # has_outputs: List[str]
    outputs: List[DataObject]
    model_config = ConfigDict(from_attributes=True)


class ReadsQCBase(PipelineStepBase):
    type: str = WorkflowActivityTypeEnum.reads_qc.value
    input_read_count: Optional[int] = None
    input_read_bases: Optional[int] = None
    output_read_count: Optional[int] = None
    output_read_bases: Optional[int] = None


class ReadsQC(PipelineStep):
    pass


class AssemblyBase(PipelineStepBase):
    scaffolds: Optional[float] = None
    contigs: Optional[float] = None
    scaf_bp: Optional[float] = None
    contig_bp: Optional[float] = None
    scaf_n50: Optional[float] = None
    scaf_l50: Optional[float] = None
    ctg_n50: Optional[float] = None
    ctg_l50: Optional[float] = None
    scaf_n90: Optional[float] = None
    scaf_l90: Optional[float] = None
    ctg_n90: Optional[float] = None
    ctg_l90: Optional[float] = None
    scaf_max: Optional[float] = None
    ctg_max: Optional[float] = None
    scaf_n_gt50k: Optional[float] = None

    # TODO: fix the data on ingest or make this optional on the schema
    scaf_l_gt50k: Optional[float] = None
    scaf_pct_gt50k: Optional[float] = None
    num_input_reads: Optional[float] = None
    num_aligned_reads: Optional[float] = None
    scaf_logsum: Optional[float] = None
    scaf_powsum: Optional[float] = None
    ctg_logsum: Optional[float] = None
    ctg_powsum: Optional[float] = None
    asm_score: Optional[float] = None
    gap_pct: Optional[float] = None
    gc_avg: Optional[float] = None
    gc_std: Optional[float] = None


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
    metaproteomics_analysis_category: str


class MetaproteomicAnalysis(PipelineStep):
    metaproteomics_analysis_category: str


class MAG(BaseModel):
    bin_name: Optional[str] = None
    number_of_contig: Optional[int] = None
    completeness: Optional[float] = None
    contamination: Optional[float] = None
    gene_count: Optional[int] = None
    bin_quality: Optional[str] = None
    num_16s: Optional[int] = None
    num_5s: Optional[int] = None
    num_23s: Optional[int] = None
    num_t_rna: Optional[int] = None


class MAGCreate(MAG):
    mags_analysis: "MAGsAnalysis"


class MAGsAnalysisBase(PipelineStepBase):
    type: str = WorkflowActivityTypeEnum.mags_analysis.value
    input_contig_num: Optional[int] = None
    too_short_contig_num: Optional[int] = None
    low_depth_contig_num: Optional[int] = None
    unbinned_contig_num: Optional[int] = None
    binned_contig_num: Optional[int] = None


class MAGsAnalysis(PipelineStep):
    type: str = WorkflowActivityTypeEnum.mags_analysis.value
    input_contig_num: Optional[int] = None
    too_short_contig_num: Optional[int] = None
    low_depth_contig_num: Optional[int] = None
    unbinned_contig_num: Optional[int] = None
    binned_contig_num: Optional[int] = None

    mags_list: List[MAG]


class NOMAnalysisBase(PipelineStepBase):
    type: str = WorkflowActivityTypeEnum.nom_analysis.value


class NOMAnalysis(PipelineStep):
    pass


class ReadBasedAnalysisBase(PipelineStepBase):
    type: str = WorkflowActivityTypeEnum.read_based_analysis.value


class ReadBasedAnalysis(PipelineStep):
    pass


class MetatranscriptomeBase(PipelineStepBase):
    type: str = WorkflowActivityTypeEnum.metatranscriptome_expression.value


class Metatranscriptome(PipelineStep):
    pass


class MetabolomicsAnalysisBase(PipelineStepBase):
    type: str = WorkflowActivityTypeEnum.metabolomics_analysis.value


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
OmicsProcessing.model_rebuild()
Biosample.model_rebuild()
MAGCreate.model_rebuild()


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


EnvoTreeNode.model_rebuild()


class EnvoTreeResponse(BaseModel):
    trees: Dict[str, List[EnvoTreeNode]]


class KeggTermListResponse(BaseModel):
    terms: List[str]


class KeggTermText(BaseModel):
    term: str
    text: str
    model_config = ConfigDict(from_attributes=True)


class KeggTermTextListResponse(BaseModel):
    terms: List[KeggTermText]


class IngestArgumentSchema(BaseModel):
    skip_annotation: bool = False
    function_limit: int = 0  # Default to no limit


class User(BaseModel):
    id: Optional[UUID] = None
    orcid: str
    name: str = ""
    email: Optional[str] = None
    is_admin: bool = False
    model_config = ConfigDict(from_attributes=True)


class LockOperationResult(BaseModel):
    success: bool
    message: str
    locked_by: Optional[User] = None
    lock_updated: Optional[datetime] = None


class VersionInfo(BaseModel):
    """Version information for the nmdc-server itself and the schemas.

    This model has default field values and is immutable because these values cannot
    change at runtime.
    """

    nmdc_server: str = __version__
    nmdc_schema: str = version("nmdc-schema")
    nmdc_submission_schema: str = version("nmdc-submission-schema")
    model_config = ConfigDict(frozen=False)
