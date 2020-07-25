from enum import Enum
from itertools import groupby
from typing import cast, Dict, Iterator, List, Literal, Tuple, Union

from pydantic import BaseModel, validator
from sqlalchemy import and_, distinct, func, or_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Query, Session
from sqlalchemy.orm.util import AliasedClass

from nmdc_server import models, schemas
from nmdc_server.models import (
    EnvBroadScaleAncestor,
    EnvBroadScaleTerm,
    EnvLocalScaleAncestor,
    EnvLocalScaleTerm,
    EnvMediumAncestor,
    EnvMediumTerm,
)
from nmdc_server.query_fields import (
    AttributeInfo,
    BiosampleAttribute,
    MetagenomeAnnotationAttribute,
    MetagenomeAssemblyAttribute,
    MetaproteomicAnalysisAttribute,
    ProjectAttribute,
    ReadsQCAttribute,
    StudyAttribute,
)


class InvalidAttributeException(Exception):
    def __init__(self, table: str, attribute: str):
        self.table = table
        self.attribute = attribute
        super(InvalidAttributeException, self).__init__(
            f"Attribute {self.attribute} not found in table {self.table}"
        )


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


class InvalidQuery(Exception):
    pass


class Operation(Enum):
    equal = "=="
    greater = ">"
    greater_equal = ">="
    less = "<"
    less_equal = "<="
    not_equal = "!="
    between = "between"


class Table(Enum):
    biosample = "biosample"
    study = "study"
    project = "project"
    env_broad_scale = "env_broad_scale"
    env_local_scale = "env_local_scale"
    env_medium = "env_medium"
    reads_qc = "reads_qc"
    metagenome_assembly = "metagenome_assembly"
    metagenome_annotation = "metagenome_annotation"
    metaproteomic_analysis = "metaproteomic_analysis"

    @property
    def model(self) -> Union[models.ModelType, AliasedClass]:
        if self == Table.biosample:
            return models.Biosample
        elif self == Table.study:
            return models.Study
        elif self == Table.project:
            return models.Project
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
        raise Exception("Unknown table")

    def query(self, db: Session) -> Query:
        if self == Table.biosample:
            query = (
                db.query(distinct(models.Biosample.id).label("id"))
                .join(models.Project)
                .join(models.Study)
                .join(models.ReadsQC, isouter=True)
                .join(models.MetagenomeAssembly, isouter=True)
                .join(models.MetagenomeAnnotation, isouter=True)
                .join(models.MetaproteomicAnalysis, isouter=True)
            )
        elif self == Table.study:
            query = (
                db.query(distinct(models.Study.id).label("id"))
                .join(models.Project, isouter=True)
                .join(models.Biosample, isouter=True)
                .join(models.ReadsQC, isouter=True)
                .join(models.MetagenomeAssembly, isouter=True)
                .join(models.MetagenomeAnnotation, isouter=True)
                .join(models.MetaproteomicAnalysis, isouter=True)
            )
        elif self == Table.project:
            query = (
                db.query(distinct(models.Project.id).label("id"))
                .join(models.Study)
                .join(models.Biosample, isouter=True)
                .join(models.ReadsQC, isouter=True)
                .join(models.MetagenomeAssembly, isouter=True)
                .join(models.MetagenomeAnnotation, isouter=True)
                .join(models.MetaproteomicAnalysis, isouter=True)
            )
        elif self == Table.reads_qc:
            query = (
                db.query(distinct(models.ReadsQC.id).label("id"))
                .join(models.Project)
                .join(models.Study)
                .join(models.Biosample, isouter=True)
                .join(models.MetagenomeAssembly, isouter=True)
                .join(models.MetagenomeAnnotation, isouter=True)
                .join(models.MetaproteomicAnalysis, isouter=True)
            )
        elif self == Table.metagenome_assembly:
            query = (
                db.query(distinct(models.MetagenomeAssembly.id).label("id"))
                .join(models.Project)
                .join(models.Study)
                .join(models.Biosample, isouter=True)
                .join(models.ReadsQC, isouter=True)
                .join(models.MetagenomeAnnotation, isouter=True)
                .join(models.MetaproteomicAnalysis, isouter=True)
            )
        elif self == Table.metagenome_annotation:
            query = (
                db.query(distinct(models.MetagenomeAnnotation.id).label("id"))
                .join(models.Project)
                .join(models.Study)
                .join(models.Biosample, isouter=True)
                .join(models.ReadsQC, isouter=True)
                .join(models.MetagenomeAssembly, isouter=True)
                .join(models.MetaproteomicAnalysis, isouter=True)
            )
        elif self == Table.metaproteomic_analysis:
            query = (
                db.query(distinct(models.MetaproteomicAnalysis.id).label("id"))
                .join(models.Project)
                .join(models.Study)
                .join(models.Biosample, isouter=True)
                .join(models.ReadsQC, isouter=True)
                .join(models.MetagenomeAssembly, isouter=True)
                .join(models.MetagenomeAnnotation, isouter=True)
            )
        else:
            raise Exception("Unknown table")
        return _join_envo(query)


AttributeType = Union[
    BiosampleAttribute,
    MetagenomeAnnotationAttribute,
    MetagenomeAssemblyAttribute,
    MetaproteomicAnalysisAttribute,
    ProjectAttribute,
    ReadsQCAttribute,
    StudyAttribute,
]


class BaseCondition(BaseModel):
    op: Operation = Operation.equal
    field: AttributeType
    value: Union[schemas.AnnotationValue, Tuple[schemas.AnnotationValue, schemas.AnnotationValue]]
    table: Table

    @validator("value")
    def validate_value_type(cls, v, values):
        if values["op"] == Operation.between:
            if not isinstance(v, tuple):
                raise ValueError("between operator requires a tuple value")
            if v[0] > v[1]:
                raise ValueError("lower bound must be less than upper bound")
        elif isinstance(v, tuple):
            raise ValueError("tuple values are only valid for between conditions")
        return v

    def compare(self):
        info: AttributeInfo = self.field.info()
        column = info.column
        if isinstance(column, JSONB) and self.op == Operation.between:
            json_field = self.column.astext  # type: ignore
            min_value = self.value[0]  # type: ignore
            max_value = self.value[0]  # type: ignore
            return and_(
                func.nmdc_compare(json_field, ">=", min_value),
                func.nmdc_compare(json_field, "<=", max_value),
            )
        elif isinstance(column, JSONB):
            json_field = self.column.astext  # type: ignore
            return func.nmdc_compare(func.nmdc_compare(json_field, self.op.value, self.value))
        elif self.op == Operation.equal:
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
        elif self.op == Operation.between:
            min_value, max_value = cast(
                Tuple[schemas.AnnotationValue, schemas.AnnotationValue], self.value
            )
            return and_(column >= min_value, column <= max_value)

    @property
    def key(self) -> str:
        return f"{self.table}:{self.field}"


class StudyCondition(BaseCondition):
    field: StudyAttribute
    table: Literal[Table.study] = Table.study


class ProjectCondition(BaseCondition):
    field: ProjectAttribute
    table: Literal[Table.project] = Table.project


class BiosampleCondition(BaseCondition):
    field: BiosampleAttribute
    table: Literal[Table.project] = Table.project


class ReadsQCCondition(BaseCondition):
    field: ReadsQCAttribute
    table: Literal[Table.project] = Table.project


class MetagenomeAssemblyCondition(BaseCondition):
    field: MetagenomeAssemblyAttribute
    table: Literal[Table.project] = Table.project


class MetagenomeAnnotationCondition(BaseCondition):
    field: MetagenomeAnnotationAttribute
    table: Literal[Table.project] = Table.project


class MetaproteomicAnalysisCondition(BaseCondition):
    field: MetaproteomicAnalysisAttribute
    table: Literal[Table.project] = Table.project


Condition = Union[
    BiosampleCondition,
    MetagenomeAnnotationCondition,
    MetagenomeAssemblyCondition,
    MetaproteomicAnalysisCondition,
    ProjectCondition,
    ReadsQCCondition,
    StudyCondition,
]


class BaseQuerySchema(BaseModel):
    conditions: List[Condition] = []

    @property
    def table(self) -> Table:
        raise Exception("Abstract class")

    @property
    def sorted_conditions(self) -> List[Condition]:
        return sorted(self.conditions, key=lambda c: c.key)

    @property
    def groups(self) -> Iterator[Tuple[str, Iterator[Condition]]]:
        return groupby(self.sorted_conditions, key=lambda c: c.key)

    def query(self, db, base_query: Query = None) -> Query:
        query = base_query or self.table.query(db)
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

    def facet_query_join(self, query: Query, attribute: AttributeType) -> Query:
        return query

    def facet(self, db: Session, attribute: AttributeType) -> Dict[schemas.AnnotationValue, int]:
        subquery = self.query(db).subquery()
        column = attribute.info().column
        query = self.facet_query_join(db.query(column, func.count(column)), attribute)
        query = query.join(subquery, self.table.model.id == subquery.c.id)
        rows = query.group_by(column)
        return {value: count for value, count in rows if value is not None}


class StudyQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.study


class ProjectQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.project


class BiosampleQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.biosample

    def facet_query_join(self, query: Query, attribute: BiosampleAttribute):  # type: ignore
        if attribute == BiosampleAttribute.env_broad_scale:
            return query.join(
                EnvBroadScaleAncestor, EnvBroadScaleTerm.id == EnvBroadScaleAncestor.ancestor_id
            ).join(
                models.Biosample, models.Biosample.env_broad_scale_id == EnvBroadScaleAncestor.id
            )
        elif attribute == BiosampleAttribute.env_local_scale:
            return query.join(
                EnvLocalScaleAncestor, EnvLocalScaleTerm.id == EnvLocalScaleAncestor.ancestor_id
            ).join(
                models.Biosample, models.Biosample.env_local_scale_id == EnvLocalScaleAncestor.id
            )
        elif attribute == BiosampleAttribute.env_medium:
            return query.join(
                EnvMediumAncestor, EnvMediumTerm.id == EnvMediumAncestor.ancestor_id
            ).join(models.Biosample, models.Biosample.env_medium_id == EnvMediumAncestor.id)
        else:
            return query


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
    conditions: List[Condition] = []


class StudyFacetQuery(SearchQuery):
    attribute: StudyAttribute


class ProjectFacetQuery(SearchQuery):
    attribute: ProjectAttribute


class BiosampleFacetQuery(SearchQuery):
    attribute: BiosampleAttribute


class ReadsQCFacetQuery(SearchQuery):
    attribute: ReadsQCAttribute


class MetagenomeAssemblyFacetQuery(SearchQuery):
    attribute: MetagenomeAssemblyAttribute


class MetagenomeAnnotationFacetQuery(SearchQuery):
    attribute: MetagenomeAnnotationAttribute


class MetaproteomicAnalysisFacetQuery(SearchQuery):
    attribute: MetaproteomicAnalysisAttribute


class StudySearchResponse(BaseSearchResponse):
    results: List[schemas.Study]


class ProjectSearchResponse(BaseSearchResponse):
    results: List[schemas.Project]


class ReadsQCSearchResponse(BaseSearchResponse):
    results: List[schemas.ReadsQC]


class MetagenomeAssemblySearchResponse(BaseSearchResponse):
    results: List[schemas.MetagenomeAssembly]


class MetagenomeAnnotationSearchResponse(BaseSearchResponse):
    results: List[schemas.MetagenomeAnnotation]


class MetaproteomicAnalysisSearchResponse(BaseSearchResponse):
    results: List[schemas.MetaproteomicAnalysis]


class FacetResponse(BaseModel):
    facets: Dict[str, int]
