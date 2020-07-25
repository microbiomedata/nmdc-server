from enum import Enum
from typing import Union

from nmdc_server import models
from nmdc_server.schemas import AttributeInfo, AttributeType


class StudyAttribute(Enum):
    principal_investigator = "principal_investigator"
    add_date = "add_date"
    mod_date = "mod_date"

    def info(self) -> AttributeInfo:
        return _study_info[self]


class ProjectAttribute(Enum):
    omics_type = "omics_type"
    instrument_name = "instrument_type"
    add_date = "add_date"
    mod_date = "mod_date"

    def info(self) -> AttributeInfo:
        return _project_info[self]


class BiosampleAttribute(Enum):
    habitat = "habitat"
    ecosystem = "ecosystem"
    ecosystem_category = "ecosystem_category"
    ecosystem_type = "ecosystem_type"
    ecosystem_subtype = "ecosystem_subtype"
    specific_ecosystem = "specific_ecosystem"
    env_broad_scale = "env_broad_scale"
    env_local_scale = "env_local_scale"
    env_medium = "env_medium"
    geo_loc_name = "geo_loc_name"
    location = "location"
    depth = "depth"
    subsurface_depth = "subsurface_depth"
    latitude = "latitude"
    longitude = "longitude"
    collection_date = "collection_date"
    add_date = "add_date"
    mod_date = "mod_date"

    def info(self) -> AttributeInfo:
        return _biosample_info[self]


class ReadsQCAttribute(Enum):
    started_at_time = "started_at_time"
    ended_at_time = "ended_at_time"
    execution_resource = "execution_resource"

    input_read_count = "input_read_count"
    input_read_bases = "input_read_bases"
    output_read_count = "output_read_count"
    output_read_bases = "output_read_bases"

    def info(self) -> AttributeInfo:
        return _reads_qc_info[self]


class MetagenomeAssemblyAttribute(Enum):
    started_at_time = "started_at_time"
    ended_at_time = "ended_at_time"
    execution_resource = "execution_resource"

    scaffolds = "scaffolds"
    contigs = "contigs"
    scaf_bp = "scaf_bp"
    contig_bp = "contig_bp"
    scaf_N50 = "scaf_N50"
    scaf_L50 = "scaf_L50"
    ctg_N50 = "ctg_N50"
    ctg_L50 = "ctg_L50"
    scaf_N90 = "scaf_N90"
    scaf_L90 = "scaf_L90"
    ctg_N90 = "ctg_N90"
    ctg_L90 = "ctg_L90"
    scaf_max = "scaf_max"
    ctg_max = "ctg_max"
    scaf_n_gt50K = "scaf_n_gt50K"
    scaf_l_gt50k = "scaf_l_gt50k"
    scaf_pct_gt50K = "scaf_pct_gt50K"
    num_input_reads = "num_input_reads"
    num_aligned_reads = "num_aligned_reads"

    scaf_logsum = "scaf_logsum"
    scaf_powsum = "scaf_powsum"
    ctg_logsum = "ctg_logsum"
    ctg_powsum = "ctg_powsum"
    asm_score = "asm_score"
    gap_pct = "gap_pct"
    gc_avg = "gc_avg"
    gc_std = "gc_std"

    def info(self) -> AttributeInfo:
        return _assembly_info[self]


class MetagenomeAnnotationAttribute(Enum):
    started_at_time = "started_at_time"
    ended_at_time = "ended_at_time"
    execution_resource = "execution_resource"

    def info(self) -> AttributeInfo:
        return _annotation_info[self]


class MetaproteomicAnalysisAttribute(Enum):
    started_at_time = "started_at_time"
    ended_at_time = "ended_at_time"
    execution_resource = "execution_resource"

    def info(self) -> AttributeInfo:
        return _analysis_info[self]


TableAttribute = Union[
    StudyAttribute,
    ProjectAttribute,
    BiosampleAttribute,
    ReadsQCAttribute,
    MetagenomeAssemblyAttribute,
    MetagenomeAnnotationAttribute,
    MetaproteomicAnalysisAttribute,
]

# fmt: off
_study_info = {
    StudyAttribute.add_date: AttributeInfo(
        name="Date added",
        column=models.Study.add_date,
        type=AttributeType.date,
    ),
    StudyAttribute.mod_date: AttributeInfo(
        name="Date modified",
        column=models.Study.mod_date,
        type=AttributeType.date,
    ),
    StudyAttribute.principal_investigator: AttributeInfo(
        name="Principal investigator",
        column=models.Study.principal_investigator_name,
    ),
}


_project_info = {
    ProjectAttribute.add_date: AttributeInfo(
        name="Date added",
        column=models.Project.add_date,
        type=AttributeType.date,
    ),
    ProjectAttribute.mod_date: AttributeInfo(
        name="Date modified",
        column=models.Project.mod_date,
        type=AttributeType.date,
    ),
    ProjectAttribute.omics_type: AttributeInfo(
        name="Omics type",
        column=models.Project.annotations["omics_type"],
    ),
    ProjectAttribute.instrument_name: AttributeInfo(
        name="Instrument name",
        column=models.Project.annotations["instrument_name"],
    ),
}


_biosample_info = {
    BiosampleAttribute.habitat: AttributeInfo(
        name="Habitat",
        column=models.Biosample.annotations["habitat"],
        group="Ecosystem",
    ),
    BiosampleAttribute.ecosystem: AttributeInfo(
        name="Ecosystem",
        column=models.Biosample.annotations["ecosystem"],
        group="Ecosystem",
    ),
    BiosampleAttribute.ecosystem_category: AttributeInfo(
        name="Ecosystem category",
        column=models.Biosample.annotations["ecosystem_category"],
        group="Ecosystem",
    ),
    BiosampleAttribute.ecosystem_type: AttributeInfo(
        name="Ecosystem type",
        column=models.Biosample.annotations["ecosystem_type"],
        group="Ecosystem",
    ),
    BiosampleAttribute.ecosystem_subtype: AttributeInfo(
        name="Ecosystem subtype",
        column=models.Biosample.annotations["ecosystem_subtype"],
        group="Ecosystem",
    ),
    BiosampleAttribute.specific_ecosystem: AttributeInfo(
        name="Specific ecosystem",
        column=models.Biosample.annotations["specific_ecosystem"],
        group="Ecosystem",
    ),
    BiosampleAttribute.specific_ecosystem: AttributeInfo(
        name="Specific ecosystem",
        column=models.Biosample.annotations["specific_ecosystem"],
        group="Ecosystem",
    ),
    BiosampleAttribute.env_broad_scale: AttributeInfo(
        name="Environmental biome",
        column=models.EnvBroadScaleTerm.label,
        group="Ecosystem",
    ),
    BiosampleAttribute.env_local_scale: AttributeInfo(
        name="Environmental feature",
        column=models.EnvLocalScaleTerm.label,
        group="Ecosystem",
    ),
    BiosampleAttribute.env_medium: AttributeInfo(
        name="Environmental material",
        column=models.EnvMediumTerm.label,
        group="Ecosystem",
    ),
    BiosampleAttribute.geo_loc_name: AttributeInfo(
        name="Location",
        column=models.Biosample.annotations["geo_loc_name"],
        group="Location",
    ),
    BiosampleAttribute.location: AttributeInfo(
        name="Site",
        column=models.Biosample.annotations["location"],
        group="Location",
    ),
    BiosampleAttribute.depth: AttributeInfo(
        name="Depth",
        column=models.Biosample.depth,
        type=AttributeType.float_,
        group="Location",
    ),
    BiosampleAttribute.subsurface_depth: AttributeInfo(
        name="Subsurface depth",
        column=models.Biosample.annotations["subsurface_depth"],
        type=AttributeType.float_,
        group="Location",
    ),
    BiosampleAttribute.latitude: AttributeInfo(
        name="Latitude",
        column=models.Biosample.latitude,
        type=AttributeType.float_,
        group="Location",
    ),
    BiosampleAttribute.longitude: AttributeInfo(
        name="Longitude",
        column=models.Biosample.longitude,
        type=AttributeType.float_,
        group="Location",
    ),
    BiosampleAttribute.collection_date: AttributeInfo(
        name="Date collected",
        column=models.Biosample.add_date,
        type=AttributeType.date,
    ),
    BiosampleAttribute.add_date: AttributeInfo(
        name="Date added",
        column=models.Biosample.add_date,
        type=AttributeType.date,
    ),
    BiosampleAttribute.mod_date: AttributeInfo(
        name="Date modified",
        column=models.Biosample.mod_date,
        type=AttributeType.date,
    ),
}

_reads_qc_info = {
    ReadsQCAttribute.started_at_time: AttributeInfo(
        name="Started at time",
        column=models.ReadsQC.started_at_time,
        type=AttributeType.date,
    ),
    ReadsQCAttribute.ended_at_time: AttributeInfo(
        name="Ended at time",
        column=models.ReadsQC.ended_at_time,
        type=AttributeType.date,
    ),
    ReadsQCAttribute.execution_resource: AttributeInfo(
        name="Execution resource",
        column=models.ReadsQC.execution_resource,
    ),
    ReadsQCAttribute.input_read_count: AttributeInfo(
        name="Input read count",
        column=models.ReadsQC.input_read_count,
        type=AttributeType.integer,
    ),
    ReadsQCAttribute.input_read_bases: AttributeInfo(
        name="Input read bases",
        column=models.ReadsQC.input_read_bases,
        type=AttributeType.integer,
    ),
    ReadsQCAttribute.output_read_count: AttributeInfo(
        name="output read count",
        column=models.ReadsQC.output_read_count,
        type=AttributeType.integer,
    ),
    ReadsQCAttribute.output_read_bases: AttributeInfo(
        name="output read bases",
        column=models.ReadsQC.output_read_bases,
        type=AttributeType.integer,
    ),
}

_assembly_info = {
    MetagenomeAssemblyAttribute.started_at_time: AttributeInfo(
        name="Started at time",
        column=models.MetagenomeAssembly.started_at_time,
        type=AttributeType.date,
    ),
    MetagenomeAssemblyAttribute.ended_at_time: AttributeInfo(
        name="Ended at time",
        column=models.MetagenomeAssembly.ended_at_time,
        type=AttributeType.date,
    ),
    MetagenomeAssemblyAttribute.execution_resource: AttributeInfo(
        name="Execution resource",
        column=models.MetagenomeAssembly.execution_resource,
    ),
    MetagenomeAssemblyAttribute.scaffolds: AttributeInfo(
        name="scaffolds",
        column=models.MetagenomeAssembly.scaffolds,
        type=AttributeType.integer,
    ),
    MetagenomeAssemblyAttribute.contigs: AttributeInfo(
        name="contigs",
        column=models.MetagenomeAssembly.contigs,
        type=AttributeType.integer,
    ),
    MetagenomeAssemblyAttribute.scaf_bp: AttributeInfo(
        name="scaf_bp",
        column=models.MetagenomeAssembly.scaf_bp,
        type=AttributeType.integer,
    ),
    MetagenomeAssemblyAttribute.contig_bp: AttributeInfo(
        name="contig_bp",
        column=models.MetagenomeAssembly.contig_bp,
        type=AttributeType.integer,
    ),
    MetagenomeAssemblyAttribute.scaf_N50: AttributeInfo(
        name="scaf_N50",
        column=models.MetagenomeAssembly.scaf_N50,
        type=AttributeType.integer,
    ),
    MetagenomeAssemblyAttribute.scaf_L50: AttributeInfo(
        name="scaf_L50",
        column=models.MetagenomeAssembly.scaf_L50,
        type=AttributeType.integer,
    ),
    MetagenomeAssemblyAttribute.ctg_N50: AttributeInfo(
        name="ctg_N50",
        column=models.MetagenomeAssembly.ctg_N50,
        type=AttributeType.integer,
    ),
    MetagenomeAssemblyAttribute.ctg_L50: AttributeInfo(
        name="ctg_L50",
        column=models.MetagenomeAssembly.ctg_L50,
        type=AttributeType.integer,
    ),
    MetagenomeAssemblyAttribute.scaf_N90: AttributeInfo(
        name="scaf_N90",
        column=models.MetagenomeAssembly.scaf_N90,
        type=AttributeType.integer,
    ),
    MetagenomeAssemblyAttribute.scaf_L90: AttributeInfo(
        name="scaf_L90",
        column=models.MetagenomeAssembly.scaf_L90,
        type=AttributeType.integer,
    ),
    MetagenomeAssemblyAttribute.ctg_N90: AttributeInfo(
        name="ctg_N90",
        column=models.MetagenomeAssembly.ctg_N90,
        type=AttributeType.integer,
    ),
    MetagenomeAssemblyAttribute.ctg_L90: AttributeInfo(
        name="ctg_L90",
        column=models.MetagenomeAssembly.ctg_L90,
        type=AttributeType.integer,
    ),
    MetagenomeAssemblyAttribute.scaf_max: AttributeInfo(
        name="scaf_max",
        column=models.MetagenomeAssembly.scaf_max,
        type=AttributeType.integer,
    ),
    MetagenomeAssemblyAttribute.ctg_max: AttributeInfo(
        name="ctg_max",
        column=models.MetagenomeAssembly.ctg_max,
        type=AttributeType.integer,
    ),
    MetagenomeAssemblyAttribute.scaf_n_gt50K: AttributeInfo(
        name="scaf_n_gt50K",
        column=models.MetagenomeAssembly.scaf_n_gt50K,
        type=AttributeType.integer,
    ),
    MetagenomeAssemblyAttribute.scaf_n_gt50K: AttributeInfo(
        name="scaf_n_gt50K",
        column=models.MetagenomeAssembly.scaf_n_gt50K,
        type=AttributeType.integer,
    ),
    MetagenomeAssemblyAttribute.scaf_pct_gt50K: AttributeInfo(
        name="scaf_pct_gt50K",
        column=models.MetagenomeAssembly.scaf_pct_gt50K,
        type=AttributeType.integer,
    ),
    MetagenomeAssemblyAttribute.num_input_reads: AttributeInfo(
        name="num_input_reads",
        column=models.MetagenomeAssembly.num_input_reads,
        type=AttributeType.integer,
    ),
    MetagenomeAssemblyAttribute.num_aligned_reads: AttributeInfo(
        name="num_aligned_reads",
        column=models.MetagenomeAssembly.num_aligned_reads,
        type=AttributeType.integer,
    ),
    MetagenomeAssemblyAttribute.scaf_logsum: AttributeInfo(
        name="scaf_logsum",
        column=models.MetagenomeAssembly.scaf_logsum,
        type=AttributeType.float_,
    ),
    MetagenomeAssemblyAttribute.scaf_powsum: AttributeInfo(
        name="scaf_powsum",
        column=models.MetagenomeAssembly.scaf_powsum,
        type=AttributeType.float_,
    ),
    MetagenomeAssemblyAttribute.ctg_logsum: AttributeInfo(
        name="ctg_logsum",
        column=models.MetagenomeAssembly.ctg_logsum,
        type=AttributeType.float_,
    ),
    MetagenomeAssemblyAttribute.ctg_powsum: AttributeInfo(
        name="ctg_powsum",
        column=models.MetagenomeAssembly.ctg_powsum,
        type=AttributeType.float_,
    ),
    MetagenomeAssemblyAttribute.asm_score: AttributeInfo(
        name="asm_score",
        column=models.MetagenomeAssembly.asm_score,
        type=AttributeType.float_,
    ),
    MetagenomeAssemblyAttribute.gap_pct: AttributeInfo(
        name="gap_pct",
        column=models.MetagenomeAssembly.gap_pct,
        type=AttributeType.float_,
    ),
    MetagenomeAssemblyAttribute.gc_avg: AttributeInfo(
        name="gc_avg",
        column=models.MetagenomeAssembly.gc_avg,
        type=AttributeType.float_,
    ),
    MetagenomeAssemblyAttribute.gc_std: AttributeInfo(
        name="gc_std",
        column=models.MetagenomeAssembly.gc_std,
        type=AttributeType.float_,
    ),
}

_annotation_info = {
    MetagenomeAnnotationAttribute.started_at_time: AttributeInfo(
        name="Started at time",
        column=models.MetagenomeAnnotation.started_at_time,
        type=AttributeType.date,
    ),
    MetagenomeAnnotationAttribute.ended_at_time: AttributeInfo(
        name="Ended at time",
        column=models.MetagenomeAnnotation.ended_at_time,
        type=AttributeType.date,
    ),
    MetagenomeAnnotationAttribute.execution_resource: AttributeInfo(
        name="Execution resource",
        column=models.MetagenomeAnnotation.execution_resource,
    ),
}

_analysis_info = {
    MetaproteomicAnalysisAttribute.started_at_time: AttributeInfo(
        name="Started at time",
        column=models.MetaproteomicAnalysis.started_at_time,
        type=AttributeType.date,
    ),
    MetaproteomicAnalysisAttribute.ended_at_time: AttributeInfo(
        name="Ended at time",
        column=models.MetaproteomicAnalysis.ended_at_time,
        type=AttributeType.date,
    ),
    MetaproteomicAnalysisAttribute.execution_resource: AttributeInfo(
        name="Execution resource",
        column=models.MetaproteomicAnalysis.execution_resource,
    ),
}
# fmt: on
