"""
This module is responsible for joining between "target tables" and "filter
tables" for the logic in query.py.

In order to generate the subquery for a particular query condition, you need to
be able to join all of the relations between those tables.  As an example if you
are search for omics_processing and are filtering on a study property, this module
provides the logic generates:

select id from omics_procession
join biosample ...
join study ...

The actual filters can then be added onto this as "where" clauses.

In general, you would need to generate N^2 different join conditions mapping
between all tables represented in `table.py`.  In practice, there is a lot of
duplicated logic that is shared in subclasses in this module.  Also, many
combinations of tables are never used and are thus unimplemented.
"""

from typing import TYPE_CHECKING, Iterable, List, Type

from sqlalchemy import func, or_
from sqlalchemy.orm import Query, Session

from nmdc_server import models
from nmdc_server.table import (
    EnvBroadScaleAncestor,
    EnvBroadScaleTerm,
    EnvLocalScaleAncestor,
    EnvLocalScaleTerm,
    EnvMediumAncestor,
    EnvMediumTerm,
    MetaPGeneFunction,
    MetaTGeneFunction,
    Table,
    workflow_execution_tables,
)

if TYPE_CHECKING:
    from nmdc_server.query import BaseConditionSchema  # noqa


envo_tables = {
    Table.env_broad_scale,
    Table.env_local_scale,
    Table.env_medium,
}

omics_processing_related_tables = {
    Table.omics_processing,
    Table.gene_function,
} | workflow_execution_tables

biosample_related_tables = {
    Table.biosample,
} | envo_tables

study_related_tables = {
    Table.study,
    Table.principal_investigator,
}


class BaseFilter:
    """Base class for generating filtered queries for conditions."""

    table: Table  # the table associated with the filter conditions

    def __init__(self, conditions: Iterable["BaseConditionSchema"] = ()):
        self.conditions = list(conditions)
        assert all([c.table == self.table for c in self.conditions]), "Invalid condition"

    def matches(
        self,
        db: Session,
        target_table: Table,
    ) -> Query:
        """Get a query representing unique id's of the target table matching the conditions."""
        query = db.query(func.distinct(target_table.model.id).label("id"))  # type: ignore
        return self._apply_conditions(query, target_table)

    def _apply_conditions(
        self,
        query: Query,
        target_table: Table,
    ) -> Query:

        filters = [c.compare() for c in self.conditions]
        return self.join(target_table, query).filter(or_(*filters))

    def join(self, target_table: Table, query: Query) -> Query:
        """Join target_table with the table associated with this filter."""
        if target_table == self.table:
            return query

        if target_table in omics_processing_related_tables:
            return self._join_omics_processing_related_tables(target_table, query)

        if target_table in biosample_related_tables:
            return self._join_biosample_related_tables(target_table, query)

        if target_table in study_related_tables:
            return self._join_study_related_tables(target_table, query)

        raise NotImplementedError()

    def _join_omics_processing_related_tables(self, target_table: Table, query: Query) -> Query:
        if target_table != Table.omics_processing:
            query = query.join(models.OmicsProcessing)

        return self.join_omics_processing(query)

    def _join_biosample_related_tables(self, target_table: Table, query: Query) -> Query:
        if target_table != Table.biosample:
            query = query.join(models.Biosample)

        query = self.join_biosample(query)
        if target_table == Table.biosample:
            return query
        if target_table in envo_tables:
            return self.join_envo(target_table, query)
        return query

    def _join_study_related_tables(self, target_table: Table, query: Query) -> Query:
        if target_table != Table.study:
            query = query.join(models.Study)
        return self.join_study(query)

    def join_envo(self, table: Table, query: Query) -> Query:
        """Join with an envo table.

        Assumes the query is already joined with the biosample table.
        """
        if table == Table.env_broad_scale:
            return query.join(
                EnvBroadScaleAncestor,
                models.Biosample.env_broad_scale_id == EnvBroadScaleAncestor.id,
            ).join(
                EnvBroadScaleTerm,
                EnvBroadScaleAncestor.ancestor_id == EnvBroadScaleTerm.id,
            )
        if table == Table.env_local_scale:
            return query.join(
                EnvLocalScaleAncestor,
                models.Biosample.env_local_scale_id == EnvLocalScaleAncestor.id,
            ).join(
                EnvLocalScaleTerm,
                EnvLocalScaleAncestor.ancestor_id == EnvLocalScaleTerm.id,
            )
        if table == Table.env_medium:
            return query.join(
                EnvMediumAncestor,
                models.Biosample.env_medium_id == EnvMediumAncestor.id,
            ).join(
                EnvMediumTerm,
                EnvMediumAncestor.ancestor_id == EnvMediumTerm.id,
            )
        return query

    def join_study(self, query: Query) -> Query:
        raise NotImplementedError()

    def join_omics_processing(self, query: Query) -> Query:
        raise NotImplementedError()

    def join_biosample(self, query: Query) -> Query:
        raise NotImplementedError()

    def join_self(self, query: Query, parent: Table) -> Query:
        if self.table == parent:
            return query
        return query.join(self.table.model)


class StudyFilter(BaseFilter):
    table = Table.study

    def join_omics_processing(self, query: Query) -> Query:
        return self.join_self(
            query.join(models.Study, models.OmicsProcessing.study_id == models.Study.id),
            Table.study,
        )

    def join_biosample(self, query: Query) -> Query:
        return self.join_self(
            query.join(models.Study, models.Biosample.study_id == models.Study.id),
            Table.study,
        )

    def join_study(self, query: Query) -> Query:
        return self.join_self(query, Table.study)


class PrincipalInvestigatorFilter(StudyFilter):
    table = Table.principal_investigator


class BiosampleFilter(BaseFilter):
    table = Table.biosample

    def join_omics_processing(self, query: Query) -> Query:
        return self.join_self(
            query.join(models.biosample_input_association).join(models.Biosample),
            Table.biosample,
        )

    def join_biosample(self, query: Query) -> Query:
        return self.join_self(query, Table.biosample)

    def join_study(self, query: Query) -> Query:
        return self.join_self(
            query.join(models.Biosample, models.Study.id == models.Biosample.study_id),
            Table.biosample,
        )

    def join_self(self, query: Query, parent: Table) -> Query:
        if self.table in envo_tables:
            return self.join_envo(self.table, query)
        return super().join_self(query, parent)

    def join_data_object(self, query: Query) -> Query:
        return self.join_omics_processing(query)


class EnvBroadScaleFilter(BiosampleFilter):
    table = Table.env_broad_scale


class EnvLocalScaleFilter(BiosampleFilter):
    table = Table.env_local_scale


class EnvMediumFilter(BiosampleFilter):
    table = Table.env_medium


class OmicsProcessingFilter(BaseFilter):
    table = Table.omics_processing

    def join_omics_processing(self, query: Query) -> Query:
        return self.join_self(query, Table.omics_processing)

    def join_biosample(self, query: Query) -> Query:
        return query.join(models.biosample_input_association).join(models.OmicsProcessing)

    def join_study(self, query: Query) -> Query:
        return self.join_self(
            query.join(models.OmicsProcessing, models.Study.id == models.OmicsProcessing.study_id),
            Table.omics_processing,
        )


workflow_filter_classes: List[Type[OmicsProcessingFilter]] = []
for table in workflow_execution_tables:
    workflow_filter_classes.append(
        type(f"{table.value}_filter", (OmicsProcessingFilter,), {"table": table})
    )


class GeneFunctionFilter(OmicsProcessingFilter):
    table = Table.gene_function

    def join(self, target_table: Table, query: Query) -> Query:
        if target_table == Table.metagenome_annotation:
            return query.join(
                models.MGAGeneFunctionAggregation,
                models.MGAGeneFunctionAggregation.metagenome_annotation_id
                == models.MetagenomeAnnotation.id,
            ).join(
                models.GeneFunction,
                models.GeneFunction.id == models.MGAGeneFunctionAggregation.gene_function_id,
            )

        query = super().join(target_table, query)
        # Use the association table to join from OmicsProcessing/DataGeneration to
        # MetagenomeAnnotation. Due to how the association table(s) are generated
        # dynamically, mypy does not know what the columns are.
        association_table = models.metagenome_annotation_data_generation_association
        return (
            query.join(
                association_table,
                association_table.data_generation_id == models.OmicsProcessing.id,  # type: ignore
            )
            .join(
                models.MetagenomeAnnotation,
                models.MetagenomeAnnotation.id
                == association_table.metagenome_annotation_id,  # type: ignore
            )
            .join(
                models.MGAGeneFunctionAggregation,
                models.MGAGeneFunctionAggregation.metagenome_annotation_id
                == models.MetagenomeAnnotation.id,
            )
            .join(
                models.GeneFunction,
                models.GeneFunction.id == models.MGAGeneFunctionAggregation.gene_function_id,
            )
        )

    def join_self(self, query: Query, parent: Table) -> Query:
        return query


class KeggFunctionFilter(GeneFunctionFilter):
    table = Table.kegg_function


class CogFunctionFilter(GeneFunctionFilter):
    table = Table.cog_function


class PfamFunctionFilter(GeneFunctionFilter):
    table = Table.pfam_function


class GoFunctionFilter(GeneFunctionFilter):
    table = Table.go_function


class MetaPGeneFunctionFilter(OmicsProcessingFilter):
    table = Table.metap_gene_function

    def join(self, target_table: Table, query: Query) -> Query:
        if target_table == Table.metaproteomic_analysis:
            return query.join(
                models.MetaPGeneFunctionAggregation,
                models.MetaPGeneFunctionAggregation.metaproteomic_analysis_id
                == models.MetaproteomicAnalysis.id,
            ).join(
                MetaPGeneFunction,
                MetaPGeneFunction.id == models.MetaPGeneFunctionAggregation.gene_function_id,
            )

        query = super().join(target_table, query)
        association_table = models.metaproteomic_analysis_data_generation_association
        return (
            query.join(
                association_table,
                association_table.data_generation_id == models.OmicsProcessing.id,  # type: ignore
            )
            .join(
                models.MetaproteomicAnalysis,
                models.MetaproteomicAnalysis.id
                == association_table.metaproteomic_analysis_id,  # type: ignore
            )
            .join(
                models.MetaPGeneFunctionAggregation,
                models.MetaPGeneFunctionAggregation.metaproteomic_analysis_id
                == models.MetaproteomicAnalysis.id,
            )
            .join(
                MetaPGeneFunction,
                MetaPGeneFunction.id == models.MetaPGeneFunctionAggregation.gene_function_id,
            )
        )

    def join_self(self, query: Query, parent: Table) -> Query:
        return query


class MetaTGeneFunctionFilter(OmicsProcessingFilter):
    table = Table.metat_gene_function

    def join(self, target_table: Table, query: Query) -> Query:
        if target_table == Table.metatranscriptome_annotation:
            return query.join(
                models.MetaTGeneFunctionAggregation,
                models.MetaTGeneFunctionAggregation.metatranscriptome_annotation_id
                == models.MetatranscriptomeAnnotation.id,
            ).join(
                MetaTGeneFunction,
                MetaTGeneFunction.id == models.MetaTGeneFunctionAggregation.gene_function_id,
            )
        query = super().join(target_table, query)
        association_table = models.metatranscriptome_annotation_data_generation_association
        return (
            query.join(
                association_table,
                association_table.data_generation_id == models.OmicsProcessing.id,  # type: ignore
            )
            .join(
                models.MetatranscriptomeAnnotation,
                models.MetatranscriptomeAnnotation.id
                == association_table.metatranscriptome_annotation_id,  # type: ignore
            )
            .join(
                models.MetaTGeneFunctionAggregation,
                models.MetaTGeneFunctionAggregation.metatranscriptome_annotation_id
                == models.MetatranscriptomeAnnotation.id,
            )
            .join(
                MetaTGeneFunction,
                MetaTGeneFunction.id == models.MetaTGeneFunctionAggregation.gene_function_id,
            )
        )

    def join_self(self, query: Query, parent: Table) -> Query:
        return query


class MetaproteomicAnalysisFilter(OmicsProcessingFilter):
    table = Table.metaproteomic_analysis

    def join_omics_processing(self, query: Query) -> Query:
        return query.join(self.table.model)

    def join_biosample(self, query: Query) -> Query:
        return (
            query.join(models.biosample_input_association)
            .join(models.OmicsProcessing)
            .join(self.table.model)
        )


def _get_all_subclasses(cls: Type[BaseFilter]) -> List[Type[BaseFilter]]:
    all_subclasses: List[Type[BaseFilter]] = []
    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(_get_all_subclasses(subclass))
    return all_subclasses


_subclasses_map = {sc.table: sc for sc in _get_all_subclasses(BaseFilter)}


def create_filter_class(table: Table, *args, **kwargs) -> BaseFilter:
    if table not in _subclasses_map:
        raise NotImplementedError(f"No filter class exists for {table.value}")
    return _subclasses_map[table](*args, **kwargs)
