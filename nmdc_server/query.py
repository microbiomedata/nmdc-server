"""
This module contains schemas that turn the query DSL into sqlalchemy query objects
for both search and faceting aggregations.
"""

import re
from datetime import datetime
from enum import Enum
from itertools import groupby
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field, PositiveInt
from sqlalchemy import ARRAY, Column, and_, cast, desc, func, inspect, or_
from sqlalchemy.orm import Query, Session, aliased, selectinload, with_expression
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql.expression import ClauseElement, intersect, union
from sqlalchemy.sql.selectable import CTE
from typing_extensions import Annotated, Literal

from nmdc_server import binning, models, schemas, schemas_submission
from nmdc_server.binning import DateBinResolution
from nmdc_server.data_object_filters import DataObjectFilter
from nmdc_server.filters import create_filter_class
from nmdc_server.multiomics import MultiomicsValue
from nmdc_server.table import (
    CogTerms,
    EnvBroadScaleAncestor,
    EnvBroadScaleTerm,
    EnvLocalScaleAncestor,
    EnvLocalScaleTerm,
    EnvMediumAncestor,
    EnvMediumTerm,
    KeggTerms,
    PfamEntries,
    Table,
)


# Custom exceptions to provide better error responses in the API.
class InvalidAttributeException(Exception):
    def __init__(self, table: str, attribute: str):
        self.table = table
        self.attribute = attribute
        super(InvalidAttributeException, self).__init__(
            f"Attribute {self.attribute} not found in table {self.table}"
        )


class InvalidFacetException(Exception):
    pass


def _join_envo_facet(query: Query, attribute: str) -> Query:
    if attribute == "env_broad_scale":
        return query.join(
            EnvBroadScaleAncestor, EnvBroadScaleTerm.id == EnvBroadScaleAncestor.ancestor_id
        ).join(models.Biosample, models.Biosample.env_broad_scale_id == EnvBroadScaleAncestor.id)
    elif attribute == "env_local_scale":
        return query.join(
            EnvLocalScaleAncestor, EnvLocalScaleTerm.id == EnvLocalScaleAncestor.ancestor_id
        ).join(models.Biosample, models.Biosample.env_local_scale_id == EnvLocalScaleAncestor.id)
    elif attribute == "env_medium":
        return query.join(
            EnvMediumAncestor, EnvMediumTerm.id == EnvMediumAncestor.ancestor_id
        ).join(models.Biosample, models.Biosample.env_medium_id == EnvMediumAncestor.id)
    else:
        raise Exception("Unknown envo attribute")


class InvalidQuery(Exception):
    pass


class Operation(Enum):
    equal = "=="
    greater = ">"
    greater_equal = ">="
    less = "<"
    less_equal = "<="
    not_equal = "!="
    like = "like"


# These dicts serve to provide special logic when filter conditions
# reference them.  They are not simple queries on attributes of the
# provided table.
_envo_keys: Dict[str, Tuple[Table, str]] = {
    "env_broad_scale": (Table.env_broad_scale, "label"),
    "env_local_scale": (Table.env_local_scale, "label"),
    "env_medium": (Table.env_medium, "label"),
}

_association_proxy_keys: Dict[str, Tuple[Any, Any]] = {
    "principal_investigator_name": (models.Study, models.PrincipalInvestigator.name),
    "metaproteomics_analysis_category": (
        models.OmicsProcessing,
        models.MetaproteomicAnalysis.metaproteomics_analysis_category,
    ),
}

_special_keys: Dict[str, Tuple[Table, str]] = {
    "study_id": (Table.study, "id"),
    "sample_id": (Table.biosample, "id"),
    "biosample_id": (Table.biosample, "id"),
    "omics_processing_id": (Table.omics_processing, "id"),
    **_envo_keys,
}

NumericValue = Union[float, int, datetime]
RangeValue = Annotated[List[schemas.AnnotationValue], Field(min_items=2, max_items=2)]


class GoldTreeValue(BaseModel):
    ecosystem: Optional[str] = None
    ecosystem_category: Optional[str] = None
    ecosystem_type: Optional[str] = None
    ecosystem_subtype: Optional[str] = None
    specific_ecosystem: Optional[str] = None


ConditionValue = Union[schemas.AnnotationValue, RangeValue, List[GoldTreeValue]]


class BaseConditionSchema(BaseModel):
    field: str
    value: ConditionValue
    table: Table

    # Determines whether the field of this query condition is a column
    # on the table or not.  For fields that are not, the query is generally
    # passed on to the "annotations" jsonb field for models that have it.
    def is_column(self) -> bool:
        m = self.table.model
        if isinstance(self.table.model, AliasedClass):
            return hasattr(self.table.model, self.field)
        return self.field in inspect(m).all_orm_descriptors.keys()

    # Generate sql clause representing the conditions.  This generally assumes
    # the correct table has already been joined into the query.
    def compare(self) -> ClauseElement:
        raise NotImplementedError("Abstract class method")

    @property
    def key(self) -> str:
        """Provide a unique key for grouping conditions on one field together."""
        return f"{self.table}:{self.field}"

    # This method originally existed because the "table" attribute was optional.  It
    # now serves to replace the table attribute for "special" fields.  For example,
    # the API uses the `biosample` table for `env_medium`, where the property actually
    # exists on a different table.
    @classmethod
    def from_schema(
        cls, condition: "BaseConditionSchema", default_table: Table
    ) -> "BaseConditionSchema":
        kwargs = condition.dict()
        if condition.field in _special_keys:
            kwargs["table"], kwargs["field"] = _special_keys[condition.field]
        elif not condition.table:
            kwargs["table"] = default_table
        return cls(**kwargs)


# This condition type represents the original DSL for comparisons.  It
# represents simple binary operators on scalar fields and is generally
# compatible with all attributes.
class SimpleConditionSchema(BaseConditionSchema):
    op: Operation = Operation.equal
    field: str
    value: schemas.AnnotationValue
    table: Table

    def compare(self) -> ClauseElement:
        model = self.table.model
        if self.is_column():
            column = getattr(model, self.field)
            if self.op == Operation.equal:
                return column == self.value
            elif self.op == Operation.greater:
                return column > self.value
            elif self.op == Operation.greater_equal:
                return column >= self.value
            elif self.op == Operation.less:
                return column < self.value
            elif self.op == Operation.less_equal:
                return column <= self.value
            elif self.op == Operation.not_equal:
                return column != self.value
            elif self.op == Operation.like:
                return column.ilike(f"%{self.value}%")
        if hasattr(model, "annotations"):
            json_field = model.annotations
        else:
            raise InvalidAttributeException(self.table.value, self.field)
        if self.op == Operation.like:
            return func.nmdc_compare(
                json_field[self.field].astext, self.op.value, f"%{self.value}%"
            )
        return func.nmdc_compare(json_field[self.field].astext, self.op.value, self.value)


# A range query that can't be achieved with simple conditions (because they are "or"-ed together).
class RangeConditionSchema(BaseConditionSchema):
    op: Literal["between"]
    field: str
    value: RangeValue
    table: Table

    def compare(self) -> ClauseElement:
        model = self.table.model
        if self.is_column():
            column = getattr(model, self.field)
            return and_(column >= self.value[0], column <= self.value[1])
        if hasattr(model, "annotations"):
            return and_(
                func.nmdc_compare(model.annotations[self.field].astext, ">=", self.value[0]),
                func.nmdc_compare(model.annotations[self.field].astext, "<=", self.value[1]),
            )
        else:
            raise InvalidAttributeException(self.table.value, self.field)


# A special condition type used on gold terms that supports hierarchical queries.
class GoldConditionSchema(BaseConditionSchema):
    table: Table  # can't do a Literal on an enum type
    value: List[GoldTreeValue]
    field: Literal["gold_tree"]
    op: Literal["tree"]

    def compare(self) -> ClauseElement:
        or_args = []
        for gold_tree in self.value:
            and_args = []
            for key, value in gold_tree.dict().items():
                if value is not None:
                    and_args.append(getattr(models.Biosample, key) == value)
            or_args.append(and_(*and_args))
        if or_args:
            return or_(*or_args)
        return or_(True)


# A special condition type on multiomics bitstrings
class MultiomicsConditionSchema(BaseConditionSchema):
    table: Table
    value: int
    field: Literal["multiomics"]
    op: Literal["has"]

    def compare(self) -> ClauseElement:
        and_args = [True]
        for omics in MultiomicsValue:
            if self.value & omics.value:
                and_args.append(models.Biosample.multiomics.op("&")(omics.value) > 0)
        return and_(*and_args)


ConditionSchema = Union[
    RangeConditionSchema,
    SimpleConditionSchema,
    GoldConditionSchema,
    MultiomicsConditionSchema,
]


def _transform_gene_term(term: tuple[str, Any]) -> str:
    if term[0].startswith("KO:K"):
        return term[0].replace("KO:K", KeggTerms.ORTHOLOGY[0])
    if term[0].startswith("COG"):
        return term[0].replace("COG", "COG:COG")
    if term[0].startswith("PF"):
        return term[0].replace("PF", "PFAM:PF")
    return term[0]


# This is the base class for all table specific queries.  It is responsible for performing
# both searches and facet aggregations.  At a high level, the queries are generated as follows:
#   1. group conditions by table/field
#   2. join all tables necessary from the target table to the filter table
#   3. generate a subquery collecting all target table id's that match any of the filters
#   4. perform an intersection on all of the subqueries
#
# The above is used in several different queries.  To search matching entities
# on the target table, you can join the id's contained in the intersection with
# the table itself.  For aggregations, it uses special select and group by clauses.
class BaseQuerySchema(BaseModel):
    conditions: List[ConditionSchema] = []

    @property
    def table(self) -> Table:
        """Return the target table of the query."""
        raise Exception("Abstract method")

    @property
    def sorted_conditions(self) -> List[BaseConditionSchema]:
        conditions = [c.__class__.from_schema(c, self.table) for c in self.conditions]
        return sorted(conditions, key=lambda c: c.key)

    @property
    def groups(self) -> Iterator[Tuple[str, Iterator[BaseConditionSchema]]]:
        return groupby(self.sorted_conditions, key=lambda c: c.key)

    def transform_condition(self, db, condition: BaseConditionSchema) -> List[BaseConditionSchema]:
        # Transform KEGG.(PATH|MODULE) queries into their respective ORTHOLOGY terms
        gene_terms = []
        gene_search_keys = [
            "Table.kegg_function:id",
            "Table.cog_function:id",
            "Table.pfam_function:id",
            "Table.go_function:id",
        ]
        if condition.key in gene_search_keys and type(condition.value) is str:
            if any([condition.value.startswith(val) for val in KeggTerms.PATHWAY[0]]):
                prefix = [val for val in KeggTerms.PATHWAY[0] if condition.value.startswith(val)][0]
                searchable_name = condition.value.replace(prefix, KeggTerms.PATHWAY[1])
                gene_terms = db.query(models.KoTermToPathway.term).filter(
                    models.KoTermToPathway.pathway.ilike(searchable_name)
                )
            elif condition.value.startswith(KeggTerms.MODULE[0]):
                searchable_name = condition.value.replace(KeggTerms.MODULE[0], KeggTerms.MODULE[1])
                gene_terms = db.query(models.KoTermToModule.term).filter(
                    models.KoTermToModule.module.ilike(searchable_name)
                )
            # Check for searches on cog or pfam as well
            elif condition.value.startswith(CogTerms.FUNCTION):
                searchable_name = condition.value.replace(CogTerms.FUNCTION, "")
                gene_terms = db.query(models.CogTermToFunction.term).filter(
                    models.CogTermToFunction.function.ilike(searchable_name)
                )
            elif condition.value.startswith(CogTerms.PATHWAY):
                searchable_name = condition.value.replace(CogTerms.PATHWAY, "")
                gene_terms = db.query(models.CogTermToPathway.term).filter(
                    models.CogTermToPathway.pathway.ilike(searchable_name)
                )
            elif condition.value.startswith(PfamEntries.CLAN):
                searchable_name = condition.value.replace(PfamEntries.CLAN, "")
                gene_terms = db.query(models.PfamEntryToClan.entry).filter(
                    models.PfamEntryToClan.clan.ilike(searchable_name)
                )
            elif condition.value.startswith("GO:"):
                gene_terms = (
                    db.query(models.GoTermToPfamEntry.entry.label("mapped_term"))
                    .filter(models.GoTermToPfamEntry.term.ilike(condition.value))
                    .union(
                        db.query(models.GoTermToKegg.kegg_term.label("mapped_term")).filter(
                            models.GoTermToKegg.term.ilike(condition.value)
                        )
                    )
                )
                term_list = list(gene_terms)
                if not term_list:
                    return [condition]
            else:
                # This is not a condition we know how to transform.
                return [condition]
            if gene_terms:
                gene_terms = [_transform_gene_term(term) for term in gene_terms]
            return [
                SimpleConditionSchema(
                    op="==",
                    field=condition.field,
                    value=term,
                    table=condition.table,
                )
                for term in gene_terms
            ]
        return [condition]

    def query(self, db) -> Query:
        """Generate a query selecting all matching id's from the target table."""
        table_re = re.compile(r"Table.(.*):.*")
        matches = [db.query(self.table.model.id.label("id"))]  # type: ignore
        has_filters = False

        for key, _conditions in self.groups:
            # Transform and flatten
            conditions = [
                c for condition in _conditions for c in self.transform_condition(db, condition)
            ]
            # If transformation eliminated the condition group, report no filters
            has_filters = len(conditions) > 0
            match = table_re.match(key)
            if not match:
                # Not an expected user error
                raise Exception("Invalid group key")
            table = Table(match.groups()[0])
            filter = create_filter_class(table, conditions)

            # Gene function queries are treated differently because they join
            # in three different places (metaT, metaG and metaP).
            if table in [
                Table.gene_function,
                Table.kegg_function,
                Table.go_function,
                Table.pfam_function,
                Table.cog_function,
            ]:
                metag_matches = filter.matches(db, self.table)
                metap_conditions = [
                    SimpleConditionSchema(
                        table=Table.metap_gene_function,
                        field=c.field,
                        value=c.value,
                    )
                    for c in conditions
                ]
                metap_filter = create_filter_class(
                    Table.metap_gene_function,
                    metap_conditions,
                )
                gene_matches = metag_matches.union(metap_filter.matches(db, self.table))

                metat_conditions = [
                    SimpleConditionSchema(
                        table=Table.metat_gene_function,
                        field=c.field,
                        value=c.value,
                    )
                    for c in conditions
                ]
                metat_filter = create_filter_class(Table.metat_gene_function, metat_conditions)
                gene_matches = gene_matches.union(metat_filter.matches(db, self.table))
                matches.append(gene_matches)
            else:
                matches.append(filter.matches(db, self.table))

        query = db.query(self.table.model.id.label("id"))  # type: ignore
        if has_filters:
            matches_query = intersect(*matches).alias("intersect")
            query = query.join(
                matches_query,
                matches_query.c.id == self.table.model.id,  # type: ignore
            )
        return query

    def execute(self, db: Session) -> Query:
        """Search for entities in the target table."""
        model = self.table.model
        subquery = self.query(db).subquery().alias("id_filter")
        return db.query(model).join(subquery, model.id == subquery.c.id)  # type: ignore

    def count(self, db: Session) -> int:
        """Return the number of matched entities for the query."""
        return self.query(db).count()

    def get_query_range(
        self,
        db: Session,
        column: Column,
        subquery: Any,
        minimum: Optional[NumericValue] = None,
        maximum: Optional[NumericValue] = None,
    ) -> Tuple[Optional[NumericValue], Optional[NumericValue]]:
        """Get the range of a numeric/datetime quantity matching the conditions.

        The API allows specifying one or both of the min/max.  This method will only
        compute the min/max if it isn't provided.
        """
        if None in [minimum, maximum]:
            row = (
                db.query(func.min(column), func.max(column))
                .join(subquery, self.table.model.id == subquery.c.id)  # type: ignore
                .first()
            )
            if row is None:
                raise InvalidFacetException("No results in the query.")
            minimum = row[0] if minimum is None else minimum
            maximum = row[1] if maximum is None else maximum
        return minimum, maximum

    def validate_binning_args(
        self,
        attribute: str,
        minimum: Optional[NumericValue] = None,
        maximum: Optional[NumericValue] = None,
        resolution: Optional[DateBinResolution] = None,
    ):
        """Raise an exception if binning arguments aren't valid for the data type."""
        # TODO: Validation like this should happen at the schema layer, but it requires refactoring
        #       so that the schema contains the table information.
        a = schemas.AttributeType
        model = self.table.model

        if attribute not in inspect(model).columns.keys():
            raise InvalidAttributeException(self.table.value, attribute)

        column = getattr(model, attribute)
        column_type = a.from_column(column)

        if column_type == a.string:
            raise InvalidFacetException("Cannot perform binned faceting on string fields")

        if minimum is not None:
            if column_type in (a.float_, a.integer) and not isinstance(minimum, (float, int)):
                raise InvalidFacetException("minimum value must be numeric")
            if column_type == a.date and not isinstance(minimum, datetime):
                raise InvalidFacetException("minimum value must be a date")

        if maximum is not None:
            if column_type in (a.float_, a.integer) and not isinstance(maximum, (float, int)):
                raise InvalidFacetException("maximum value must be numeric")
            if column_type == a.date and not isinstance(maximum, datetime):
                raise InvalidFacetException("maximum value must be a date")

        if resolution is not None and column_type != a.date:
            raise InvalidFacetException("resolution argument only valid for date fields")

    def binned_facet(
        self,
        db: Session,
        attribute: str,
        minimum: Optional[NumericValue] = None,
        maximum: Optional[NumericValue] = None,
        **kwargs,
    ) -> Tuple[List[NumericValue], List[int]]:
        """Perform a binned faceting aggregation on an attribute."""
        model: Any = self.table.model
        self.validate_binning_args(attribute, minimum, maximum, kwargs.get("resolution"))

        column = getattr(model, attribute)
        subquery = self.query(db).subquery()

        try:
            min_, max_ = self.get_query_range(db, column, subquery, minimum, maximum)
        except InvalidFacetException:
            return [], []

        # the only way for min/max to be none is if the were no matches to the query
        if min_ is None or max_ is None:
            return [], []

        # Generate bins to use in the query
        bins: List[NumericValue]
        if "num_bins" in kwargs:
            bins = binning.range_bins(min_, max_, kwargs["num_bins"])  # type: ignore
        elif "resolution" in kwargs:
            bins = binning.datetime_bins(min_, max_, kwargs["resolution"])  # type: ignore

        # generate the binned aggregation
        bucket = func.width_bucket(column, cast(bins, ARRAY(column.type)))
        query = db.query(bucket, func.count(column))
        query = query.join(subquery, model.id == subquery.c.id)
        rows = query.group_by(bucket)
        result = [0] * (len(bins) - 1)

        # coerce the results into the output format... we need special handling for
        # values outside the given min/max
        # see documentation at https://www.postgresql.org/docs/12/functions-math.html
        count_above_maximum = 0
        for row in rows:
            if row[0] is not None and 1 <= row[0] < len(bins):
                result[row[0] - 1] = row[1]
            if row[0] == len(bins):
                count_above_maximum = row[1]

        if maximum is None:
            result[-1] += count_above_maximum

        return bins, result

    # TODO: This method will always return all values of the attribute matching
    # the query.  For attributes with a lot of unique values, this could be too
    # much data.  Consider limiting the results in the future.
    def facet(self, db: Session, attribute: str) -> Dict[schemas.AnnotationValue, int]:
        """Perform simple faceting on an attribute."""
        model: Any = self.table.model

        # special joins need to be performed for faceting on either envo or
        # association proxies.
        join_ap = False
        join_envo = False
        if attribute in _envo_keys and self.table == Table.biosample:
            table, field = _envo_keys[attribute]
            column = getattr(table.model, field)
            join_envo = True
        elif attribute in inspect(model).columns.keys():
            column = getattr(model, attribute)
        elif (
            attribute in _association_proxy_keys
            and self.table.model == _association_proxy_keys[attribute][0]
        ):
            model, column = _association_proxy_keys[attribute]
            join_ap = True
        elif hasattr(model, "annotations"):
            column = model.annotations[attribute]
        else:
            raise InvalidAttributeException(self.table.value, attribute)

        # generate the subquery of id's matching the filters and join with the
        # aggregation query
        subquery = self.query(db).subquery()
        query = db.query(column, func.count(column))

        # join additional tables if necessary
        if join_envo:
            query = _join_envo_facet(query, attribute)
        elif join_ap:
            query = query.join(model)
        query = query.join(subquery, model.id == subquery.c.id)

        # collect the results
        rows = query.group_by(column)
        return {value: count for value, count in rows if value is not None}


class StudyQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.study

    # The following private methods inject subqueries into Study `query_expressions`.
    def _count_omics_data_query(self, db: Session, query_schema: BaseQuerySchema) -> Query:
        """Generate a query counting matching omics_processing types."""
        workflow_model = query_schema.table.model
        aliased_workflow_model = aliased(workflow_model)
        table_name = workflow_model.__tablename__  # type: ignore
        was_informed_by_table = models.workflow_activity_to_data_generation_map[table_name]

        op_alias = aliased(models.OmicsProcessing)
        biosample_alias = aliased(models.Biosample)

        subquery = query_schema.query(db).subquery()

        q = (
            db.query(
                op_alias.study_id.label(f"{table_name}_study_id"),
                func.count(func.distinct(aliased_workflow_model.id)).label(f"{table_name}_count"),  # type: ignore
            )
            .select_from(op_alias)
            .join(biosample_alias, op_alias.biosample_inputs)
            .join(was_informed_by_table, was_informed_by_table.c.data_generation_id == op_alias.id)
            .join(
                aliased_workflow_model,
                aliased_workflow_model.id == was_informed_by_table.c[f"{table_name}_id"]
            )
            .join(subquery, subquery.c.id == aliased_workflow_model.id)  # type: ignore
            .group_by(op_alias.study_id)
        )
        return q

    def _count_omics_processing_summary(
        self, db: Session, conditions: List[ConditionSchema]
    ) -> Query:
        """Aggregate omics types into a custom jsonb response."""
        op_summary_alias = aliased(models.OmicsProcessing)
        biosample_alias = aliased(models.Biosample)

        subquery = OmicsProcessingQuerySchema(conditions=conditions).query(db).subquery()
        query = (
            db.query(
                op_summary_alias.annotations["omics_type"].astext.label("omics_processing_type"),
                func.count(func.distinct(op_summary_alias.id)).label("omics_processing_count"),
                op_summary_alias.study_id.label("omics_processing_study_id_sub"),
            )
            .join(subquery, subquery.c.id == op_summary_alias.id)
            .join(biosample_alias, op_summary_alias.biosample_inputs)
            .filter(op_summary_alias.annotations["omics_type"] != None)
            .group_by(
                op_summary_alias.study_id,
                op_summary_alias.annotations["omics_type"].astext,
            )
        ).subquery()
        return db.query(
            func.jsonb_agg(
                func.jsonb_build_object(
                    "type",
                    query.c.omics_processing_type,
                    "count",
                    query.c.omics_processing_count,
                )
            ).label("omics_processing_summary"),
            query.c.omics_processing_study_id_sub.label("omics_processing_study_id"),
        ).group_by(query.c.omics_processing_study_id_sub)

    def _inject_omics_data_summary(self, db: Session, query: Query) -> Query:
        """Insert query expressions for custom aggregations."""
        # Add an aggregation for each omics processing type.
        aggs = []
        for omics_class in workflow_search_classes:
            pipeline_model = omics_class().table.model
            table_name = pipeline_model.__tablename__  # type: ignore
            filter_conditions = [
                c
                for c in self.conditions
                if c.table.value in {"omics_processing", table_name, "biosample"}
            ]

            # generate a filtered subquery of the given omics type
            query_schema = omics_class(conditions=filter_conditions)
            omics_subquery = self._count_omics_data_query(db, query_schema).subquery()
            study_id = getattr(omics_subquery.c, f"{table_name}_study_id")
            query = query.join(
                omics_subquery,
                self.table.model.id == study_id,  # type: ignore
                isouter=True,
            )
            aggs.append(
                func.json_build_object(
                    "type", table_name, "count", getattr(omics_subquery.c, f"{table_name}_count")
                )
            )

        # Here we only insert filter conditions that are actually relevant for
        # this aggregation.  This reduces the complexity of subquery greatly.
        op_filter_conditions = [
            c
            for c in self.conditions
            if c.table.value
            in {"omics_processing", "biosample", "gene_function", "metaproteomic_analysis"}
        ]
        op_summary_subquery = self._count_omics_processing_summary(
            db, op_filter_conditions
        ).subquery()
        query = query.join(
            op_summary_subquery,
            op_summary_subquery.c.omics_processing_study_id == models.Study.id,
            isouter=True,
        )

        aggregation = func.json_build_array(*aggs)
        return query.populate_existing().options(
            with_expression(models.Study.omics_counts, aggregation),
            with_expression(
                models.Study.omics_processing_counts,
                op_summary_subquery.c.omics_processing_summary,
            ),
        )

    def query(self, db: Session):
        study_query = super().query(db)
        biosample_condition_exists = any(
            [condition.table == Table.biosample for condition in self.conditions]
        )
        omics_condition_exists = any(
            [condition.table == Table.omics_processing for condition in self.conditions]
        )
        if biosample_condition_exists:
            sample_query = BiosampleQuerySchema(conditions=self.conditions).query(db)
            studies_from_sample_query = sample_query.with_entities(
                models.Biosample.study_id
            ).distinct()
            study_query = study_query.where(  # type: ignore
                self.table.model.id.in_(studies_from_sample_query)  # type: ignore
            )
        elif omics_condition_exists:
            omics_query = OmicsProcessingQuerySchema(conditions=self.conditions).query(db)
            studies_from_omics_query = omics_query.with_entities(
                models.OmicsProcessing.study_id
            ).distinct()
            study_query = study_query.where(  # type: ignore
                self.table.model.id.in_(studies_from_omics_query)  # type: ignore
            )
        return study_query

    def execute(self, db: Session) -> Query:
        sample_subquery = BiosampleQuerySchema(conditions=self.conditions).query(db).subquery()
        sample_count = (
            db.query(
                models.Biosample.study_id.label("study_id"),
                func.count(models.Biosample.id).label("sample_count"),
            )
            .join(sample_subquery, models.Biosample.id == sample_subquery.c.id)
            .group_by(models.Biosample.study_id)
        ).subquery()
        model = self.table.model
        subquery = self.query(db).subquery()
        return self._inject_omics_data_summary(
            db,
            db.query(model)
            .join(subquery, model.id == subquery.c.id)  # type: ignore
            .join(sample_count, model.id == sample_count.c.study_id, isouter=True)  # type: ignore
            .order_by(models.Study.annotations["title"].astext)
            .options(with_expression(models.Study.sample_count, sample_count.c.sample_count)),
        )


class OmicsProcessingQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.omics_processing

    def facet(self, db: Session, attribute: str) -> Dict[schemas.AnnotationValue, int]:
        if attribute == "omics_type":
            annotations_column = models.OmicsProcessing.annotations
            id_column = models.OmicsProcessing.poolable_replicates_manifest_id
            query = self.query(db)
            aggregated_query = query.with_entities(
                func.count(func.distinct(id_column)).label("id_count"),
                annotations_column["omics_type"].astext,
            ).group_by(annotations_column["omics_type"].astext)
            return {value: count for count, value in aggregated_query if value is not None}
        return super().facet(db, attribute)

    def omics_processing_for_biosample_ids(self, db: Session, biosample_ids):
        # Do the normal query with the conditions
        query = self.execute(db)
        # Join to association table to get biosample IDs
        query_by_sample_ids = (
            query.join(models.biosample_input_association)
            # Filter to only include bisoample ids in the given list
            .filter(models.biosample_input_association.c.biosample_id.in_(biosample_ids))
        )
        return query_by_sample_ids


class BiosampleQuerySchema(BaseQuerySchema):
    data_object_filter: List[DataObjectFilter] = []

    @property
    def table(self) -> Table:
        return Table.biosample

    def query(self, db: Session):
        sample_query = super().query(db)
        if any([condition.table == Table.omics_processing for condition in self.conditions]):
            omics_query = OmicsProcessingQuerySchema(conditions=self.conditions).query(db)
            samples_from_omics_query = (
                omics_query.join(models.biosample_input_association)
                .with_entities(models.biosample_input_association.c.biosample_id)
                .distinct()
            )
            sample_query = sample_query.where(  # type: ignore
                self.table.model.id.in_(samples_from_omics_query)  # type: ignore
            )
        return sample_query

    def execute(self, db: Session, prefetch_omics_processing_data: bool = False) -> Query:
        model = self.table.model
        subquery = self.query(db).subquery()
        biosample_query = (
            db.query(model)
            .join(subquery, model.id == subquery.c.id)  # type: ignore
            .order_by(desc(self.table.model.multiomics))  # type: ignore
        )

        if prefetch_omics_processing_data:
            from nmdc_server.models import workflow_activity_types

            biosample_query = biosample_query.options(
                selectinload(models.Biosample.omics_processing).selectinload(
                    models.OmicsProcessing.outputs
                ),
                selectinload(models.Biosample.omics_processing).selectinload(
                    models.OmicsProcessing.biosample_inputs
                ),
            )

            for model in workflow_activity_types:
                biosample_query = biosample_query.options(
                    selectinload(models.Biosample.omics_processing)
                    .selectinload(getattr(models.OmicsProcessing, model.__tablename__))  # type: ignore[attr-defined] # noqa: E501
                    .selectinload(model.outputs)  # type: ignore[attr-defined]
                )

                # The MAGsAnalysis specifically needs to also prefetch the mags_list
                if model == models.MAGsAnalysis:
                    biosample_query = biosample_query.options(
                        selectinload(models.Biosample.omics_processing)
                        .selectinload(getattr(models.OmicsProcessing, model.__tablename__))  # type: ignore[attr-defined] # noqa: E501
                        .selectinload(model.mags_list)  # type: ignore[attr-defined]
                    )

        return biosample_query


class ReadsQCQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.reads_qc


class MetatranscriptomeQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.metatranscriptome


class MetagenomeAssemblyQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.metagenome_assembly


class MetagenomeAnnotationQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.metagenome_annotation


class MetatranscriptomeAssemblyQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.metatranscriptome_assembly


class MetatranscriptomeAnnotationQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.metatranscriptome_annotation


class MetaproteomicAnalysisQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.metaproteomic_analysis


class MAGsAnalysisQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.mags_analysis


class ReadBasedAnalysisQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.read_based_analysis


class NOMAnalysisQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.nom_analysis


class MetabolomicsAnalysisQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.metabolomics_analysis


class DataObjectAggregation(BaseModel):
    count: int
    size: int


class DataObjectQuerySchema(BaseQuerySchema):
    data_object_filter: List[DataObjectFilter] = []

    # Perform the normal query operation, but adds in an additional filter on
    # entities from data_object_filter.
    def query(self, db: Session) -> Query:
        omics_processing_qs = OmicsProcessingQuerySchema(conditions=self.conditions)
        op_cte = omics_processing_qs.query(db).cte()

        subqueries = [
            self._data_object_filter_subquery(db, f, op_cte) for f in self.data_object_filter
        ]
        union_query = union(
            db.query(models.DataObject.id.label("id")).filter(False),  # type: ignore
            *subqueries,  # type: ignore
        ).subquery()
        return db.query(models.DataObject).join(
            union_query, models.DataObject.id == union_query.c.id
        )

    def execute(self, db: Session) -> Query:
        return self.query(db)

    # WARNING: This logic is duplicated in the DataObject.is_selected method.
    def _data_object_filter_subquery(
        self, db: Session, filter: DataObjectFilter, op_cte: CTE
    ) -> Query:
        """Create a subquery that selects from a data object filter condition."""
        query = db.query(models.DataObject.id.label("id")).join(
            op_cte,
            models.DataObject.omics_processing_id == op_cte.c.id,
        )
        if filter.workflow:
            query = query.filter(models.DataObject.workflow_type == filter.workflow.value)

        if filter.file_type:
            query = query.filter(models.DataObject.file_type == filter.file_type)

        query = query.filter(models.DataObject.url != None)  # noqa
        return query

    def aggregate(self, db: Session) -> DataObjectAggregation:
        """Return the number of files and total size of matched data objects."""
        subquery = (
            self.query(db)
            .filter(models.DataObject.url != None)
            .filter(models.DataObject.file_size_bytes != None)
            .subquery()
        )
        row = db.query(
            func.count(subquery.c.id),
            func.sum(func.coalesce(subquery.c.file_size_bytes, 0)),
        ).first()
        if not row:
            return DataObjectAggregation(count=0, size=0)
        return DataObjectAggregation(count=row[0] or 0, size=row[1] or 0)

    @property
    def table(self) -> Table:
        return Table.data_object


class BaseSearchResponse(BaseModel):
    count: int


class BiosampleSearchResponse(BaseSearchResponse):
    results: List[schemas.Biosample]


class SearchQuery(BaseModel):
    conditions: List[ConditionSchema] = []


class ConditionResultSchema(SimpleConditionSchema):
    model_config = ConfigDict(from_attributes=True)


class FacetQuery(SearchQuery):
    attribute: str


class BiosampleSearchQuery(SearchQuery):
    data_object_filter: List[DataObjectFilter] = []


class BinnedRangeFacetQuery(FacetQuery):
    minimum: Optional[NumericValue] = None
    maximum: Optional[NumericValue] = None
    num_bins: PositiveInt


class BinnedDateFacetQuery(FacetQuery):
    minimum: Optional[datetime] = None
    maximum: Optional[datetime] = None
    resolution: DateBinResolution


BinnedFacetQuery = Union[BinnedRangeFacetQuery, BinnedDateFacetQuery]


class StudySearchResponse(BaseSearchResponse):
    results: List[schemas.Study]
    total: Optional[int] = None


class OmicsProcessingSearchResponse(BaseSearchResponse):
    results: List[schemas.OmicsProcessing]


class DataObjectSearchResponse(BaseSearchResponse):
    results: List[schemas.DataObject]


class FacetResponse(BaseModel):
    facets: Dict[schemas.AnnotationValue, int]


class BinnedFacetResponse(BaseModel):
    facets: List[int]
    bins: List[NumericValue]


class MetadataSubmissionResponse(BaseSearchResponse):
    results: List[schemas_submission.SubmissionMetadataSchema]


class UserResponse(BaseSearchResponse):
    results: List[schemas.User]


workflow_search_classes = [
    ReadsQCQuerySchema,
    MetagenomeAssemblyQuerySchema,
    MetagenomeAnnotationQuerySchema,
    MetatranscriptomeAssemblyQuerySchema,
    MetatranscriptomeAnnotationQuerySchema,
    MetaproteomicAnalysisQuerySchema,
    MAGsAnalysisQuerySchema,
    ReadBasedAnalysisQuerySchema,
    NOMAnalysisQuerySchema,
    MetabolomicsAnalysisQuerySchema,
    MetatranscriptomeQuerySchema,
]
