from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote
from uuid import UUID

from pint import Unit
from pydantic import BaseModel, Field, validator
from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, String

from nmdc_server import models


# The order in the this union is significant... it will coerce
# valid datetime strings into datetime objects while falling
# back to ordinary strings.  Also, we never want numeric types
# to be interpreted as dates.
AnnotationValue = Union[float, int, datetime, str]


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
    name: str
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
    ecosystem_type: str
    ecosystem_subtype: str
    specific_ecosystem: str

    class Config:
        orm_mode = True


class EnvironmentGeospatialAggregation(BaseModel):
    count: int
    latitude: float
    longitude: float
    ecosystem: Optional[str]
    ecosystem_category: Optional[str]

    class Config:
        orm_mode = True


# study
class StudyBase(AnnotatedBase):
    principal_investigator_websites: List[str] = []
    publication_dois: List[str] = []
    gold_name: str = ""
    gold_description: str = ""
    scientific_objective: str = ""
    add_date: Optional[datetime]
    mod_date: Optional[datetime]
    doi: str

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
    principal_investigator_id: UUID


class OmicsCounts(BaseModel):
    type: str
    count: int

    @validator("count", pre=True, always=True)
    def insert_zero(cls, v):
        return v or 0


class Study(StudyBase):
    open_in_gold: Optional[str]
    principal_investigator_name: str
    principal_investigator_image_url: str
    sample_count: Optional[int]
    omics_counts: Optional[List[OmicsCounts]]
    omics_processing_counts: Optional[List[OmicsCounts]]
    publication_doi_info: Dict[str, Any]

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
    longitude: float = Field(..., gt=-180, le=180)
    latitude: float = Field(..., ge=-90, le=90)
    add_date: Optional[datetime]
    mod_date: Optional[datetime]

    collection_date: Union[datetime, date, None]
    ecosystem: str
    ecosystem_category: str
    ecosystem_type: str
    ecosystem_subtype: str
    specific_ecosystem: str


class BiosampleCreate(BiosampleBase):
    pass


class Biosample(BiosampleBase):
    open_in_gold: Optional[str]
    env_broad_scale: Optional[EnvoTerm]
    env_local_scale: Optional[EnvoTerm]
    env_medium: Optional[EnvoTerm]
    env_broad_scale_terms: List[str] = []
    env_local_scale_terms: List[str] = []
    env_medium_terms: List[str] = []

    omics_processing: List["OmicsProcessing"]
    multiomics: int

    class Config:
        orm_mode = True


# omics_processing
class OmicsProcessingBase(AnnotatedBase):
    study_id: Optional[str]
    biosample_id: Optional[str]
    add_date: Optional[datetime]
    mod_date: Optional[datetime]


class OmicsProcessingCreate(OmicsProcessingBase):
    pass


class OmicsProcessing(OmicsProcessingBase):
    open_in_gold: Optional[str]

    omics_data: List["OmicsTypes"]
    outputs: List["DataObject"]

    class Config:
        orm_mode = True


# data_object
class DataObjectBase(BaseModel):
    id: str
    name: str
    description: str = ""
    file_size_bytes: int
    md5_checksum: Optional[str]
    url: Optional[str]
    downloads: int


class DataObjectCreate(DataObjectBase):
    pass


class DataObject(DataObjectBase):
    class Config:
        orm_mode = True

    @validator("url")
    def replace_url(cls, url, values):
        id_str = quote(values["id"])
        return f"/api/data_object/{id_str}/download" if url else None


class GeneFunction(BaseModel):
    class Config:
        orm_mode = True

    id: str


class MGAGeneFunction(BaseModel):
    class Config:
        orm_mode = True

    gene_function_id: str
    subject: str


class PipelineStepBase(BaseModel):
    id: str
    name: str = ""
    type: str
    git_url: str
    started_at_time: Union[datetime, date]
    ended_at_time: Union[datetime, date]
    execution_resource: str
    omics_processing_id: str


class PipelineStep(PipelineStepBase):
    # has_inputs: List[str]
    # has_outputs: List[str]
    outputs: List[DataObject]

    class Config:
        orm_mode = True


class ReadsQCBase(PipelineStepBase):
    type: str = "nmdc:ReadQCAnalysis"
    input_read_count: int
    input_read_bases: int
    output_read_count: int
    output_read_bases: int


class ReadsQC(PipelineStep):
    pass


class MetagenomeAssemblyBase(PipelineStepBase):
    type: str = "nmdc:MetagenomeAssembly"
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

    # TODO: fix the data on ingest or make this optional on the schema
    scaf_l_gt50k: int = 0
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
    type: str = "nmdc:MetagenomeAnnotation"


class MetagenomeAnnotation(PipelineStep):
    gene_functions: List[MGAGeneFunction]


class MetaproteomicAnalysisBase(PipelineStepBase):
    type: str = "nmdc:MetaproteomicAnalysis"


class MetaproteomicAnalysis(PipelineStep):
    pass


class PeptideMGAGeneFunction(BaseModel):
    subject: str
    gene_function: str


class MetaprotemoicPeptide(BaseModel):
    peptide_sequence: str
    peptide_sum_masic_abundance: int
    peptide_spectral_count: int
    best_protein: str
    min_q_value: float

    best_protein_object: "MGAGeneFunction"


class MAG(BaseModel):
    bin_name: str
    number_of_contig: int
    completeness: float
    contamination: float
    gene_count: int
    bin_quality: str
    num_16s: int
    num_5s: int
    num_23s: int
    num_tRNA: int


class MAGCreate(MAG):
    mags_analysis: "MAGsAnalysis"


class MAGsAnalysisBase(PipelineStepBase):
    type: str = "nmdc:MAGsAnalysis"
    input_contig_num: int
    too_short_contig_num: int
    lowDepth_contig_num: int
    unbinned_contig_num: int
    binned_contig_num: int


class MAGsAnalysis(PipelineStep):
    type: str = "nmdc:MAGsAnalysis"
    input_contig_num: int
    too_short_contig_num: int
    lowDepth_contig_num: int
    unbinned_contig_num: int
    binned_contig_num: int

    mags_list: List[MAG]


class NOMAnalysisBase(PipelineStepBase):
    type: str = "nmdc:NOMAnalysis"
    used: str


class NOMAnalysis(PipelineStep):
    pass


class ReadBasedAnalysisBase(PipelineStepBase):
    type: str = "nmdc:ReadBasedAnalysis"


class ReadBasedAnalysis(PipelineStep):
    pass


class MetabolomicsAnalysisBase(PipelineStepBase):
    type: str = "nmdc:MetabolomicsAnalysis"
    used: str
    has_calibration: str


class MetabolomicsAnalysis(PipelineStep):
    pass


OmicsTypes = Union[
    ReadsQC,
    MetagenomeAnnotation,
    MetagenomeAssembly,
    MetaproteomicAnalysis,
    MAGsAnalysis,
    NOMAnalysis,
    ReadBasedAnalysis,
    MetabolomicsAnalysis,
]
OmicsProcessing.update_forward_refs()
Biosample.update_forward_refs()
MAGCreate.update_forward_refs()
MetaprotemoicPeptide.update_forward_refs()


class FileDownloadBase(BaseModel):
    ip: str
    user_agent: str
    orcid: str
    data_object_id: str


class FileDownload(FileDownloadBase):
    id: str
    created: datetime


class FileDownloadCreate(FileDownloadBase):
    pass
