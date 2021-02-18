from datetime import datetime
from enum import Enum
from itertools import groupby
import re
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

from pydantic import BaseModel, PositiveInt
from sqlalchemy import and_, ARRAY, cast, Column, func, inspect, or_
from sqlalchemy.orm import Query, Session, with_expression
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql.expression import ClauseElement, intersect
from typing_extensions import Literal

from nmdc_server import binning, models, schemas
from nmdc_server.binning import DateBinResolution
from nmdc_server.filters import create_filter_class
from nmdc_server.table import (
    EnvBroadScaleAncestor,
    EnvBroadScaleTerm,
    EnvLocalScaleAncestor,
    EnvLocalScaleTerm,
    EnvMediumAncestor,
    EnvMediumTerm,
    Table,
)


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


_envo_keys: Dict[str, Tuple[Table, str]] = {
    "env_broad_scale": (Table.env_broad_scale, "label"),
    "env_local_scale": (Table.env_local_scale, "label"),
    "env_medium": (Table.env_medium, "label"),
}

_association_proxy_keys: Dict[str, Tuple[Any, Any]] = {
    "principal_investigator_name": (models.Study, models.PrincipalInvestigator.name),
}

_special_keys: Dict[str, Tuple[Table, str]] = {
    "study_id": (Table.study, "id"),
    "sample_id": (Table.biosample, "id"),
    "biosample_id": (Table.biosample, "id"),
    "project_id": (Table.project, "id"),
    **_envo_keys,
}


NumericValue = Union[float, int, datetime]
RangeValue = Tuple[schemas.AnnotationValue, schemas.AnnotationValue]


class GoldTreeValue(BaseModel):
    ecosystem: Optional[str]
    ecosystem_category: Optional[str]
    ecosystem_type: Optional[str]
    ecosystem_subtype: Optional[str]
    specific_ecosystem: Optional[str]


ConditionValue = Union[schemas.AnnotationValue, RangeValue, List[GoldTreeValue]]


class BaseConditionSchema(BaseModel):
    field: str
    value: ConditionValue
    table: Table

    def is_column(self) -> bool:
        m = self.table.model
        if isinstance(self.table.model, AliasedClass):
            return hasattr(self.table.model, self.field)
        return self.field in inspect(m).all_orm_descriptors.keys()

    def compare(self) -> ClauseElement:
        raise NotImplementedError("Abstract class method")

    @property
    def key(self) -> str:
        return f"{self.table}:{self.field}"

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
        if hasattr(model, "annotations"):
            json_field = model.annotations  # type: ignore
        else:
            raise InvalidAttributeException(self.table.value, self.field)
        return func.nmdc_compare(json_field[self.field].astext, self.op.value, self.value)


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
                func.nmdc_compare(
                    model.annotations[self.field].astext, ">=", self.value[0]  # type: ignore
                ),
                func.nmdc_compare(
                    model.annotations[self.field].astext, "<=", self.value[1]  # type: ignore
                ),
            )
        else:
            raise InvalidAttributeException(self.table.value, self.field)


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
        return or_(*or_args)


ConditionSchema = Union[RangeConditionSchema, SimpleConditionSchema, GoldConditionSchema]


class BaseQuerySchema(BaseModel):
    conditions: List[ConditionSchema] = []

    @property
    def table(self) -> Table:
        raise Exception("Abstract method")

    @property
    def sorted_conditions(self) -> List[BaseConditionSchema]:
        conditions = [c.__class__.from_schema(c, self.table) for c in self.conditions]
        return sorted(conditions, key=lambda c: c.key)

    @property
    def groups(self) -> Iterator[Tuple[str, Iterator[BaseConditionSchema]]]:
        return groupby(self.sorted_conditions, key=lambda c: c.key)

    def query(self, db) -> Query:
        table_re = re.compile(r"Table.(.*):.*")
        matches = [db.query(self.table.model.id.label("id"))]  # type: ignore
        has_filters = False

        for key, _conditions in self.groups:
            conditions = list(_conditions)
            has_filters = True
            match = table_re.match(key)
            if not match:
                # Not an expected user error
                raise Exception("Invalid group key")
            table = Table(match.groups()[0])
            filter = create_filter_class(table, conditions)

            if table == Table.gene_function:
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
                matches.append(metag_matches.union(metap_filter.matches(db, self.table)))
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
        model = self.table.model
        subquery = self.query(db).subquery().alias("id_filter")
        return db.query(model).join(subquery, model.id == subquery.c.id)  # type: ignore

    def count(self, db: Session) -> int:
        return self.query(db).count()

    def get_query_range(
        self,
        db: Session,
        column: Column,
        subquery: Any,
        minimum: NumericValue = None,
        maximum: NumericValue = None,
    ) -> Tuple[NumericValue, NumericValue]:
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
        return minimum, maximum  # type: ignore

    def validate_binning_args(
        self,
        attribute: str,
        minimum: NumericValue = None,
        maximum: NumericValue = None,
        resolution: DateBinResolution = None,
    ):
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
        minimum: NumericValue = None,
        maximum: NumericValue = None,
        **kwargs,
    ) -> Tuple[List[NumericValue], List[int]]:
        model: Any = self.table.model
        self.validate_binning_args(attribute, minimum, maximum, kwargs.get("resolution"))

        column = getattr(model, attribute)
        subquery = self.query(db).subquery()

        try:
            min_, max_ = self.get_query_range(db, column, subquery, minimum, maximum)
        except InvalidFacetException:
            return [], []

        bins: List[NumericValue]
        if "num_bins" in kwargs:
            bins = binning.range_bins(min_, max_, kwargs["num_bins"])  # type: ignore
        elif "resolution" in kwargs:
            bins = binning.datetime_bins(min_, max_, kwargs["resolution"])  # type: ignore

        bucket = func.width_bucket(column, cast(bins, ARRAY(column.type)))
        query = db.query(bucket, func.count(column))
        query = query.join(subquery, model.id == subquery.c.id)
        rows = query.group_by(bucket)
        result = [0] * (len(bins) - 1)

        count_above_maximum = 0
        for row in rows:
            if row[0] is not None and 1 <= row[0] < len(bins):
                result[row[0] - 1] = row[1]
            if row[0] == len(bins):
                count_above_maximum = row[1]

        if maximum is None:
            result[-1] += count_above_maximum

        return bins, result

    def facet(self, db: Session, attribute: str) -> Dict[schemas.AnnotationValue, int]:
        model: Any = self.table.model
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

        subquery = self.query(db).subquery()
        query = db.query(column, func.count(column))
        if join_envo:
            query = _join_envo_facet(query, attribute)
        elif join_ap:
            query = query.join(model)
        query = query.join(subquery, model.id == subquery.c.id)
        rows = query.group_by(column)
        return {value: count for value, count in rows if value is not None}


class StudyQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.study

    def _count_omics_data_query(self, db: Session, query_schema: BaseQuerySchema) -> Query:
        model = query_schema.table.model
        table_name = model.__tablename__  # type: ignore

        subquery = query_schema.query(db).subquery()

        q = (
            db.query(
                models.Project.study_id.label(f"{table_name}_study_id"),
                func.count(model.id).label(f"{table_name}_count"),  # type: ignore
            )
            .join(model, isouter=True)
            .join(subquery, subquery.c.id == model.id)  # type: ignore
            .group_by(models.Project.study_id)
        )
        return q

    def _count_omics_processing_summary(
        self, db: Session, conditions: List[ConditionSchema]
    ) -> Query:
        subquery = ProjectQuerySchema(conditions=conditions).query(db).subquery()
        query = (
            db.query(
                models.Project.annotations["omics_type"].astext.label("omics_processing_type"),
                func.count(models.Project.id).label("omics_processing_count"),
                models.Project.study_id.label("omics_processing_study_id_sub"),
            )
            .join(subquery, subquery.c.id == models.Project.id)
            .filter(models.Project.annotations["omics_type"] != None)
            .group_by(models.Project.study_id, models.Project.annotations["omics_type"].astext)
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
            models.Project.study_id.label("omics_processing_study_id"),
        ).group_by(models.Project.study_id)

    def _inject_omics_data_summary(self, db: Session, query: Query) -> Query:
        aggs = []
        for omics_class in workflow_search_classes:
            pipeline_model = omics_class().table.model
            table_name = pipeline_model.__tablename__  # type: ignore
            filter_conditions = [
                c for c in self.conditions if c.table.value in {"project", table_name, "biosample"}
            ]

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

        op_filter_conditions = [
            c for c in self.conditions if c.table.value in {"project", "biosample"}
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
            .options(with_expression(models.Study.sample_count, sample_count.c.sample_count)),
        )


class ProjectQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.project


class BiosampleQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.biosample


class ReadsQCQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.reads_qc


class MetagenomeAssemblyQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.metagenome_assembly


class MetagenomeAnnotationQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.metagenome_annotation


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


class BaseSearchResponse(BaseModel):
    count: int


class BiosampleSearchResponse(BaseSearchResponse):
    results: List[schemas.Biosample]


class SearchQuery(BaseModel):
    conditions: List[ConditionSchema] = []


class FacetQuery(SearchQuery):
    attribute: str


class BinnedRangeFacetQuery(FacetQuery):
    minimum: Optional[NumericValue]
    maximum: Optional[NumericValue]
    num_bins: PositiveInt


class BinnedDateFacetQuery(FacetQuery):
    minimum: Optional[datetime]
    maximum: Optional[datetime]
    resolution: DateBinResolution


BinnedFacetQuery = Union[BinnedRangeFacetQuery, BinnedDateFacetQuery]


class StudySearchResponse(BaseSearchResponse):
    results: List[schemas.Study]


class ProjectSearchResponse(BaseSearchResponse):
    results: List[schemas.Project]


class DataObjectSearchResponse(BaseSearchResponse):
    results: List[schemas.DataObject]


class ReadsQCSearchResponse(BaseSearchResponse):
    results: List[schemas.ReadsQC]


class MetagenomeAssemblySearchResponse(BaseSearchResponse):
    results: List[schemas.MetagenomeAssembly]


class MetagenomeAnnotationSearchResponse(BaseSearchResponse):
    results: List[schemas.MetagenomeAnnotation]


class MetaproteomicAnalysisSearchResponse(BaseSearchResponse):
    results: List[schemas.MetaproteomicAnalysis]


class MAGsAnalysisSearchResponse(BaseSearchResponse):
    results: List[schemas.MAGsAnalysis]


class ReadBasedAnalysisSearchResponse(BaseSearchResponse):
    results: List[schemas.ReadBasedAnalysis]


class NOMAnalysisSearchResponse(BaseSearchResponse):
    results: List[schemas.NOMAnalysis]


class MetabolomicsAnalysisSearchResponse(BaseSearchResponse):
    results: List[schemas.MetabolomicsAnalysis]


class FacetResponse(BaseModel):
    facets: Dict[schemas.AnnotationValue, int]


class BinnedFacetResponse(BaseModel):
    facets: List[int]
    bins: List[NumericValue]


workflow_search_classes = [
    ReadsQCQuerySchema,
    MetagenomeAssemblyQuerySchema,
    MetagenomeAnnotationQuerySchema,
    MetaproteomicAnalysisQuerySchema,
    MAGsAnalysisQuerySchema,
    ReadBasedAnalysisQuerySchema,
    NOMAnalysisQuerySchema,
    MetabolomicsAnalysisQuerySchema,
]
