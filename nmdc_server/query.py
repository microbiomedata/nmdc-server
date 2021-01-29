from datetime import datetime
from enum import Enum
from itertools import groupby
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

from pydantic import BaseModel, PositiveInt
from sqlalchemy import and_, ARRAY, cast, Column, distinct, func, inspect, or_
from sqlalchemy.orm import aliased, Query, Session, with_expression
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql.expression import ClauseElement
from typing_extensions import Literal

from nmdc_server import binning, models, schemas
from nmdc_server.binning import DateBinResolution

EnvBroadScale = aliased(models.EnvoTerm)
EnvBroadScaleAncestor = aliased(models.EnvoAncestor)
EnvBroadScaleTerm = aliased(models.EnvoTerm)
EnvLocalScale = aliased(models.EnvoTerm)
EnvLocalScaleAncestor = aliased(models.EnvoAncestor)
EnvLocalScaleTerm = aliased(models.EnvoTerm)
EnvMedium = aliased(models.EnvoTerm)
EnvMediumAncestor = aliased(models.EnvoAncestor)
EnvMediumTerm = aliased(models.EnvoTerm)


class InvalidAttributeException(Exception):
    def __init__(self, table: str, attribute: str):
        self.table = table
        self.attribute = attribute
        super(InvalidAttributeException, self).__init__(
            f"Attribute {self.attribute} not found in table {self.table}"
        )


class InvalidFacetException(Exception):
    pass


def _join_envo(query: Query) -> Query:
    return (
        query.join(
            EnvBroadScaleAncestor,
            models.Biosample.env_broad_scale_id == EnvBroadScaleAncestor.id,
            isouter=True,
        )
        .join(
            EnvBroadScaleTerm,
            EnvBroadScaleAncestor.ancestor_id == EnvBroadScaleTerm.id,
            isouter=True,
        )
        .join(
            EnvLocalScaleAncestor,
            models.Biosample.env_local_scale_id == EnvLocalScaleAncestor.id,
            isouter=True,
        )
        .join(
            EnvLocalScaleTerm,
            EnvLocalScaleAncestor.ancestor_id == EnvLocalScaleTerm.id,
            isouter=True,
        )
        .join(
            EnvMediumAncestor, models.Biosample.env_medium_id == EnvMediumAncestor.id, isouter=True
        )
        .join(EnvMediumTerm, EnvMediumAncestor.ancestor_id == EnvMediumTerm.id, isouter=True)
    )


def _join_workflow_execution(query: Query) -> Query:
    return (
        query.join(models.ReadsQC, isouter=True)
        .join(models.MetagenomeAssembly, isouter=True)
        .join(models.MetagenomeAnnotation, isouter=True)
        .join(models.MetaproteomicAnalysis, isouter=True)
    )


def _join_gene_function(query: Query) -> Query:
    return query.join(
        models.MGAGeneFunction,
        models.MGAGeneFunction.metagenome_annotation_id == models.MetagenomeAnnotation.id,
        isouter=True,
    ).join(models.GeneFunction, isouter=True)


def _join_common(query: Query) -> Query:
    return _join_envo(query)


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


class Table(Enum):
    biosample = "biosample"
    study = "study"
    project = "project"
    data_object = "data_object"
    env_broad_scale = "env_broad_scale"
    env_local_scale = "env_local_scale"
    env_medium = "env_medium"
    reads_qc = "reads_qc"
    metagenome_assembly = "metagenome_assembly"
    metagenome_annotation = "metagenome_annotation"
    metaproteomic_analysis = "metaproteomic_analysis"
    principal_investigator = "principal_investigator"
    gene_function = "gene_function"

    @property
    def model(self) -> Union[models.ModelType, AliasedClass]:  # noqa: fix complexity
        if self == Table.biosample:
            return models.Biosample
        elif self == Table.study:
            return models.Study
        elif self == Table.project:
            return models.Project
        elif self == Table.data_object:
            return models.DataObject
        elif self == Table.env_broad_scale:
            return EnvBroadScaleTerm
        elif self == Table.env_local_scale:
            return EnvLocalScaleTerm
        elif self == Table.env_medium:
            return EnvMediumTerm
        elif self == Table.reads_qc:
            return models.ReadsQC
        elif self == Table.metagenome_assembly:
            return models.MetagenomeAssembly
        elif self == Table.metagenome_annotation:
            return models.MetagenomeAnnotation
        elif self == Table.metaproteomic_analysis:
            return models.MetaproteomicAnalysis
        elif self == Table.gene_function:
            return models.GeneFunction
        raise Exception("Unknown table")

    def query(self, db: Session) -> Query:
        if self == Table.biosample:
            query = _join_workflow_execution(
                db.query(distinct(models.Biosample.id).label("id"))
                .join(models.Project, isouter=True)
                .join(models.DataObject, isouter=True)
                .join(models.Study, models.Biosample.study_id == models.Study.id)
                .join(models.PrincipalInvestigator)
            )
        elif self == Table.study:
            query = _join_workflow_execution(
                db.query(distinct(models.Study.id).label("id"))
                .join(models.PrincipalInvestigator)
                .join(models.Biosample, models.Biosample.study_id == models.Study.id, isouter=True)
                .join(models.Project, models.Biosample.study_id == models.Study.id, isouter=True)
                .join(models.DataObject, isouter=True)
            )
        elif self == Table.project:
            query = _join_workflow_execution(
                db.query(distinct(models.Project.id).label("id"))
                .join(models.DataObject, isouter=True)
                .join(models.Biosample, isouter=True)  # until biosample_id is no longer nullable
                .join(models.Study, models.Study.id == models.Project.study_id, isouter=True)
                .join(models.PrincipalInvestigator, isouter=True)
            )
        elif self == Table.reads_qc:
            query = (
                db.query(distinct(models.ReadsQC.id).label("id"))
                .join(models.Project)
                .join(models.DataObject, isouter=True)
                .join(models.Biosample, isouter=True)
                .join(models.Study, models.Study.id == models.Project.study_id)
                .join(models.PrincipalInvestigator)
                .join(models.MetagenomeAssembly, isouter=True)
                .join(models.MetagenomeAnnotation, isouter=True)
                .join(models.MetaproteomicAnalysis, isouter=True)
            )
        elif self == Table.metagenome_assembly:
            query = (
                db.query(distinct(models.MetagenomeAssembly.id).label("id"))
                .join(models.Project)
                .join(models.DataObject, isouter=True)
                .join(models.Biosample, isouter=True)
                .join(models.Study, models.Study.id == models.Project.study_id)
                .join(models.PrincipalInvestigator)
                .join(models.ReadsQC, isouter=True)
                .join(models.MetagenomeAnnotation, isouter=True)
                .join(models.MetaproteomicAnalysis, isouter=True)
            )
        elif self == Table.metagenome_annotation:
            query = (
                db.query(distinct(models.MetagenomeAnnotation.id).label("id"))
                .join(models.Project)
                .join(models.DataObject, isouter=True)
                .join(models.Biosample, isouter=True)
                .join(models.Study, models.Study.id == models.Project.study_id)
                .join(models.PrincipalInvestigator)
                .join(models.ReadsQC, isouter=True)
                .join(models.MetagenomeAssembly, isouter=True)
                .join(models.MetaproteomicAnalysis, isouter=True)
            )
        elif self == Table.metaproteomic_analysis:
            query = (
                db.query(distinct(models.MetaproteomicAnalysis.id).label("id"))
                .join(models.Project)
                .join(models.DataObject, isouter=True)
                .join(models.Biosample, isouter=True)
                .join(models.Study, models.Study.id == models.Project.study_id)
                .join(models.PrincipalInvestigator)
                .join(models.ReadsQC, isouter=True)
                .join(models.MetagenomeAssembly, isouter=True)
                .join(models.MetagenomeAnnotation, isouter=True)
            )
        elif self == Table.data_object:
            query = (
                db.query(distinct(models.DataObject.id).label("id"))
                .join(models.Project)
                .join(models.Biosample, isouter=True)
                .join(models.Study, models.Study.id == models.Project.study_id)
                .join(models.PrincipalInvestigator)
                .join(models.ReadsQC, isouter=True)
                .join(models.MetagenomeAssembly, isouter=True)
                .join(models.MetagenomeAnnotation, isouter=True)
                .join(models.MetaproteomicAnalysis, isouter=True)
            )

        else:
            raise Exception("Unknown table")
        return _join_common(query)


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
        if isinstance(m, AliasedClass):
            m = inspect(m).class_
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
        return func.nmdc_compare(
            json_field[self.field].astext, self.op.value, self.value  # type: ignore
        )


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

    def query(self, db, base_query: Query = None) -> Query:
        query = base_query or self.table.query(db)
        if any([c.table == Table.gene_function for c in self.conditions]):
            query = _join_gene_function(query)
        for _, conditions in self.groups:
            filters = [c.compare() for c in conditions]
            query = query.filter(or_(*filters))

        return query

    def execute(self, db: Session) -> Query:
        model = self.table.model
        subquery = self.query(db).subquery()
        return db.query(model).join(subquery, model.id == subquery.c.id)

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
                .join(subquery, self.table.model.id == subquery.c.id)
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
        join_envo = False
        join_ap = False
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
        table_name = model.__tablename__
        subquery = query_schema.query(db).subquery()
        return (
            db.query(
                models.Project.study_id.label(f"{table_name}_study_id"),
                func.count(model.id).label(f"{table_name}_count"),
            )
            .join(model, isouter=True)
            .join(subquery, model.project_id == models.Project.id, isouter=True)  # type: ignore
            .group_by(models.Project.study_id)
        )

    def _inject_omics_data_summary(self, db: Session, query: Query) -> Query:
        omics_classes = [
            ReadsQCQuerySchema,
            MetagenomeAssemblyQuerySchema,
            MetagenomeAnnotationQuerySchema,
            MetaproteomicAnalysisQuerySchema,
        ]

        aggs = []
        for omics_class in omics_classes:
            query_schema = omics_class(conditions=self.conditions)
            table_name = query_schema.table.model.__tablename__
            omics_subquery = self._count_omics_data_query(db, query_schema).subquery()
            study_id = getattr(omics_subquery.c, f"{table_name}_study_id")
            query = query.join(omics_subquery, self.table.model.id == study_id, isouter=True)
            aggs.append(
                func.json_build_object(
                    "type", table_name, "count", getattr(omics_subquery.c, f"{table_name}_count")
                )
            )

        aggregation = func.json_build_array(*aggs)
        return query.populate_existing().options(
            with_expression(models.Study.omics_counts, aggregation)
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
            .join(subquery, model.id == subquery.c.id)
            .join(sample_count, model.id == sample_count.c.study_id, isouter=True)
            .options(with_expression(models.Study.sample_count, sample_count.c.sample_count)),
        )


class ProjectQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.project


class DataObjectQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.data_object


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


class FacetResponse(BaseModel):
    facets: Dict[schemas.AnnotationValue, int]


class BinnedFacetResponse(BaseModel):
    facets: List[int]
    bins: List[NumericValue]
