from enum import Enum
from typing import Optional

from pydantic import BaseModel


class WorkflowActivityTypeEnum(Enum):
    reads_qc = "nmdc:ReadQCAnalysisActivity"
    metagenome_assembly = "nmdc:MetagenomeAssembly"
    metagenome_annotation = "nmdc:MetagenomeAnnotation"
    metaproteomic_analysis = "nmdc:MetaProteomicAnalysis"
    mags_analysis = "nmdc:MAGsAnalysisActivity"
    read_based_analysis = "nmdc:ReadbasedAnalysis"
    nom_analysis = "nmdc:NomAnalysisActivity"
    metabolomics_analysis = "nmdc:MetabolomicsAnalysisActivity"
    raw_data = "nmdc:RawData"


class DataObjectFilter(BaseModel):
    workflow: Optional[WorkflowActivityTypeEnum]
    file_type: Optional[str]
