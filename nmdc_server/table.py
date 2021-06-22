from enum import Enum
from typing import Dict, Union

from sqlalchemy.orm import aliased
from sqlalchemy.orm.util import AliasedClass

from nmdc_server import models


EnvBroadScaleAncestor = aliased(models.EnvoAncestor)
EnvBroadScaleTerm = aliased(models.EnvoTerm)
EnvLocalScaleAncestor = aliased(models.EnvoAncestor)
EnvLocalScaleTerm = aliased(models.EnvoTerm)
EnvMediumAncestor = aliased(models.EnvoAncestor)
EnvMediumTerm = aliased(models.EnvoTerm)
MetaPGeneFunction = aliased(models.GeneFunction)


class Table(Enum):
    biosample = "biosample"
    study = "study"
    omics_processing = "omics_processing"
    reads_qc = "reads_qc"
    metagenome_assembly = "metagenome_assembly"
    metagenome_annotation = "metagenome_annotation"
    metaproteomic_analysis = "metaproteomic_analysis"
    mags_analysis = "mags_analysis"
    nom_analysis = "nom_analysis"
    read_based_analysis = "read_based_analysis"
    metabolomics_analysis = "metabolomics_analysis"
    gene_function = "gene_function"
    metap_gene_function = "metap_gene_function"
    data_object = "data_object"

    env_broad_scale = "env_broad_scale"
    env_local_scale = "env_local_scale"
    env_medium = "env_medium"

    principal_investigator = "principal_investigator"

    @property
    def model(self) -> Union[models.ModelType, AliasedClass]:
        if self not in _table_model_map:
            raise Exception("Unknown table")
        return _table_model_map[self]


DataObjectRaw = aliased(models.DataObject)
DataObjectReadsQC = aliased(models.DataObject)
DataObjectMetagenomeAssembly = aliased(models.DataObject)
DataObjectMetagenomeAnnotation = aliased(models.DataObject)
DataObjectMetaproteomicAnalysis = aliased(models.DataObject)
DataObjectMagsAnalysis = aliased(models.DataObject)
DataObjectReadBasedAnalysis = aliased(models.DataObject)
DataObjectMetabolomicsAnalysis = aliased(models.DataObject)


_table_model_map: Dict[Table, Union[models.ModelType, AliasedClass]] = {
    Table.biosample: models.Biosample,
    Table.study: models.Study,
    Table.omics_processing: models.OmicsProcessing,
    Table.reads_qc: models.ReadsQC,
    Table.metagenome_assembly: models.MetagenomeAssembly,
    Table.metagenome_annotation: models.MetagenomeAnnotation,
    Table.metaproteomic_analysis: models.MetaproteomicAnalysis,
    Table.mags_analysis: models.MAGsAnalysis,
    Table.nom_analysis: models.NOMAnalysis,
    Table.read_based_analysis: models.ReadBasedAnalysis,
    Table.metabolomics_analysis: models.MetabolomicsAnalysis,
    Table.gene_function: models.GeneFunction,
    Table.metap_gene_function: MetaPGeneFunction,
    Table.env_broad_scale: EnvBroadScaleTerm,
    Table.env_local_scale: EnvLocalScaleTerm,
    Table.env_medium: EnvMediumTerm,
    Table.principal_investigator: models.PrincipalInvestigator,
    Table.data_object: models.DataObject,
}

workflow_execution_tables = {
    Table.reads_qc,
    Table.metagenome_assembly,
    Table.metagenome_annotation,
    Table.metaproteomic_analysis,
    Table.mags_analysis,
    Table.nom_analysis,
    Table.read_based_analysis,
    Table.metabolomics_analysis,
}
