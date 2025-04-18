"""
This module contains enums that map from serialized table representations to
actual database models (or aliased representations).
"""

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
MetaTGeneFunction = aliased(models.GeneFunction)


class KeggTerms:
    ORTHOLOGY = ("KEGG.ORTHOLOGY:K", "K")
    PATHWAY = (
        [
            "KEGG.PATHWAY:MAP",
            "KEGG.PATHWAY:EC",
            "KEGG.PATHWAY:RN",
            "KEGG.PATHWAY:KO",
        ],
        "MAP",
    )
    MODULE = ("KEGG.MODULE:M", "M")


class CogTerms:
    FUNCTION = "COG.FUNCTION:"
    PATHWAY = "COG.PATHWAY:"


class PfamEntries:
    ENTRY = "PFAM.ENTRY:"
    CLAN = "PFAM.CLAN:"


class Table(Enum):
    biosample = "biosample"
    study = "study"
    omics_processing = "omics_processing"
    reads_qc = "reads_qc"
    metagenome_assembly = "metagenome_assembly"
    metagenome_annotation = "metagenome_annotation"
    metatranscriptome_assembly = "metatranscriptome_assembly"
    metatranscriptome_annotation = "metatranscriptome_annotation"
    metaproteomic_analysis = "metaproteomic_analysis"
    mags_analysis = "mags_analysis"
    nom_analysis = "nom_analysis"
    read_based_analysis = "read_based_analysis"
    metabolomics_analysis = "metabolomics_analysis"
    metatranscriptome = "metatranscriptome"
    metap_gene_function = "metap_gene_function"
    metat_gene_function = "metat_gene_function"
    data_object = "data_object"

    env_broad_scale = "env_broad_scale"
    env_local_scale = "env_local_scale"
    env_medium = "env_medium"

    gene_function = "gene_function"
    kegg_function = "kegg_function"
    cog_function = "cog_function"
    pfam_function = "pfam_function"
    go_function = "go_function"

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
DataObjectMetatranscriptome = aliased(models.Metatranscriptome)
DataObjectMetatranscriptomeAssembly = aliased(models.DataObject)
DataObjectMetatranscriptomeAnnotation = aliased(models.DataObject)


_table_model_map: Dict[Table, Union[models.ModelType, AliasedClass]] = {
    Table.biosample: models.Biosample,
    Table.study: models.Study,
    Table.omics_processing: models.OmicsProcessing,
    Table.reads_qc: models.ReadsQC,
    Table.metagenome_assembly: models.MetagenomeAssembly,
    Table.metatranscriptome_assembly: models.MetatranscriptomeAssembly,
    Table.metagenome_annotation: models.MetagenomeAnnotation,
    Table.metatranscriptome_annotation: models.MetatranscriptomeAnnotation,
    Table.metaproteomic_analysis: models.MetaproteomicAnalysis,
    Table.mags_analysis: models.MAGsAnalysis,
    Table.nom_analysis: models.NOMAnalysis,
    Table.read_based_analysis: models.ReadBasedAnalysis,
    Table.metatranscriptome: models.Metatranscriptome,
    Table.metabolomics_analysis: models.MetabolomicsAnalysis,
    Table.gene_function: models.GeneFunction,
    Table.kegg_function: models.GeneFunction,
    Table.cog_function: models.GeneFunction,
    Table.pfam_function: models.GeneFunction,
    Table.go_function: models.GeneFunction,
    Table.metap_gene_function: MetaPGeneFunction,
    Table.metat_gene_function: MetaTGeneFunction,
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
    Table.metatranscriptome_assembly,
    Table.metatranscriptome_annotation,
    Table.metaproteomic_analysis,
    Table.mags_analysis,
    Table.nom_analysis,
    Table.read_based_analysis,
    Table.metabolomics_analysis,
    Table.metatranscriptome,
}
