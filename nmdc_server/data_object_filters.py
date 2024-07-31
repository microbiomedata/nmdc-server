import re
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from nmdc_server import models

# Nginx's mod_zip can only server local files.  To get arround this limitation,
# we set up local proxies to all remote hosts.
#   https://www.nginx.com/resources/wiki/modules/zip/#remote-upstreams
# This means that we can only handle known prefixes.  This must be checked
# on ingest and any additional hosts added to the nginx config.
# TODO: There is probably a way to automate this using nginx pattern matching.
data_url_hosts = [
    (re.compile("^https://data.microbiomedata.org(/data)?"), "/data"),
    (re.compile("^https://nmdcdemo.emsl.pnnl.gov"), "/nmdcdemo"),
]


def get_local_data_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    for r, v in data_url_hosts:
        if r.match(url):
            return r.sub(v, url)
    return None


class WorkflowActivityTypeEnum(Enum):
    mags_analysis = "nmdc:MagsAnalysis"
    metabolomics_analysis = "nmdc:MetabolomicsAnalysis"
    metagenome_assembly = "nmdc:MetagenomeAssembly"
    metagenome_annotation = "nmdc:MetagenomeAnnotation"
    metaproteomic_analysis = "nmdc:MetaproteomicAnalysis"
    metatranscriptome = "nmdc:MetatranscriptomeAnalysis"
    metatranscriptome_assembly = "nmdc:MetatranscriptomeAssembly"
    metatranscriptome_annotation = "nmdc:MetatranscriptomeAnnotation"
    nom_analysis = "nmdc:NomAnalysis"
    raw_data = "nmdc:RawData"
    read_based_analysis = "nmdc:ReadBasedTaxonomyAnalysis"
    reads_qc = "nmdc:ReadQcAnalysis"

    @property
    def model(self):
        return _workflow_enum_to_model[self]

    @property
    def output_association(self):
        return _workflow_enum_to_output_association[self]


_workflow_enum_to_model = {
    WorkflowActivityTypeEnum.reads_qc: models.ReadsQC,
    WorkflowActivityTypeEnum.metagenome_assembly: models.MetagenomeAssembly,
    WorkflowActivityTypeEnum.metagenome_annotation: models.MetagenomeAnnotation,
    WorkflowActivityTypeEnum.metatranscriptome_assembly: models.MetatranscriptomeAssembly,
    WorkflowActivityTypeEnum.metatranscriptome_annotation: models.MetatranscriptomeAnnotation,
    WorkflowActivityTypeEnum.metaproteomic_analysis: models.MetaproteomicAnalysis,
    WorkflowActivityTypeEnum.mags_analysis: models.MAGsAnalysis,
    WorkflowActivityTypeEnum.read_based_analysis: models.ReadBasedAnalysis,
    WorkflowActivityTypeEnum.nom_analysis: models.NOMAnalysis,
    WorkflowActivityTypeEnum.metabolomics_analysis: models.MetabolomicsAnalysis,
    WorkflowActivityTypeEnum.raw_data: models.OmicsProcessing,
    WorkflowActivityTypeEnum.metatranscriptome: models.Metatranscriptome,
}

_mpa = WorkflowActivityTypeEnum.metaproteomic_analysis

_workflow_enum_to_output_association = {
    WorkflowActivityTypeEnum.reads_qc: models.reads_qc_output_association,
    WorkflowActivityTypeEnum.metagenome_assembly: models.metagenome_assembly_output_association,
    WorkflowActivityTypeEnum.metagenome_annotation: models.metagenome_annotation_output_association,
    WorkflowActivityTypeEnum.metatranscriptome_assembly: models.metatranscriptome_assembly_output_association,  # noqa: E501
    WorkflowActivityTypeEnum.metatranscriptome_annotation: models.metatranscriptome_annotation_output_association,  # noqa: E501
    _mpa: models.metaproteomic_analysis_output_association,
    WorkflowActivityTypeEnum.mags_analysis: models.mags_analysis_output_association,
    WorkflowActivityTypeEnum.read_based_analysis: models.read_based_analysis_output_association,
    WorkflowActivityTypeEnum.nom_analysis: models.nom_analysis_output_association,
    WorkflowActivityTypeEnum.metabolomics_analysis: models.metabolomics_analysis_output_association,
    WorkflowActivityTypeEnum.raw_data: models.omics_processing_output_association,
    WorkflowActivityTypeEnum.metatranscriptome: models.metabolomics_analysis_output_association,
}


class DataObjectFilter(BaseModel):
    workflow: Optional[WorkflowActivityTypeEnum]
    file_type: Optional[str]
