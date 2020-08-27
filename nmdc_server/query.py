from enum import Enum
from itertools import groupby
from typing import Any, cast, Dict, Iterator, List, Tuple, Union

from pydantic import BaseModel, validator
from sqlalchemy import and_, distinct, func, inspect, or_
from sqlalchemy.orm import aliased, Query, Session
from sqlalchemy.orm.util import AliasedClass

from nmdc_server import models, schemas

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
    between = "between"


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

    @property
    def model(self) -> Union[models.ModelType, AliasedClass]:
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
        raise Exception("Unknown table")

    def query(self, db: Session) -> Query:
        if self == Table.biosample:
            query = (
                db.query(distinct(models.Biosample.id).label("id"))
                .join(models.Project)
                .join(models.DataObject, isouter=True)
                .join(models.Study)
                .join(models.PrincipalInvestigator)
                .join(models.ReadsQC, isouter=True)
                .join(models.MetagenomeAssembly, isouter=True)
                .join(models.MetagenomeAnnotation, isouter=True)
                .join(models.MetaproteomicAnalysis, isouter=True)
            )
        elif self == Table.study:
            query = (
                db.query(distinct(models.Study.id).label("id"))
                .join(models.PrincipalInvestigator)
                .join(models.Project, isouter=True)
                .join(models.DataObject, isouter=True)
                .join(models.Biosample, isouter=True)
                .join(models.ReadsQC, isouter=True)
                .join(models.MetagenomeAssembly, isouter=True)
                .join(models.MetagenomeAnnotation, isouter=True)
                .join(models.MetaproteomicAnalysis, isouter=True)
            )
        elif self == Table.project:
            query = (
                db.query(distinct(models.Project.id).label("id"))
                .join(models.DataObject, isouter=True)
                .join(models.Study)
                .join(models.PrincipalInvestigator)
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
                .join(models.DataObject, isouter=True)
                .join(models.Study)
                .join(models.PrincipalInvestigator)
                .join(models.Biosample, isouter=True)
                .join(models.MetagenomeAssembly, isouter=True)
                .join(models.MetagenomeAnnotation, isouter=True)
                .join(models.MetaproteomicAnalysis, isouter=True)
            )
        elif self == Table.metagenome_assembly:
            query = (
                db.query(distinct(models.MetagenomeAssembly.id).label("id"))
                .join(models.Project)
                .join(models.DataObject, isouter=True)
                .join(models.Study)
                .join(models.PrincipalInvestigator)
                .join(models.Biosample, isouter=True)
                .join(models.ReadsQC, isouter=True)
                .join(models.MetagenomeAnnotation, isouter=True)
                .join(models.MetaproteomicAnalysis, isouter=True)
            )
        elif self == Table.metagenome_annotation:
            query = (
                db.query(distinct(models.MetagenomeAnnotation.id).label("id"))
                .join(models.Project)
                .join(models.DataObject, isouter=True)
                .join(models.Study)
                .join(models.PrincipalInvestigator)
                .join(models.Biosample, isouter=True)
                .join(models.ReadsQC, isouter=True)
                .join(models.MetagenomeAssembly, isouter=True)
                .join(models.MetaproteomicAnalysis, isouter=True)
            )
        elif self == Table.metaproteomic_analysis:
            query = (
                db.query(distinct(models.MetaproteomicAnalysis.id).label("id"))
                .join(models.Project)
                .join(models.DataObject, isouter=True)
                .join(models.Study)
                .join(models.PrincipalInvestigator)
                .join(models.Biosample, isouter=True)
                .join(models.ReadsQC, isouter=True)
                .join(models.MetagenomeAssembly, isouter=True)
                .join(models.MetagenomeAnnotation, isouter=True)
            )
        elif self == Table.data_object:
            query = (
                db.query(distinct(models.DataObject.id).label("id"))
                .join(models.Project)
                .join(models.Study)
                .join(models.PrincipalInvestigator)
                .join(models.Biosample, isouter=True)
                .join(models.ReadsQC, isouter=True)
                .join(models.MetagenomeAssembly, isouter=True)
                .join(models.MetagenomeAnnotation, isouter=True)
                .join(models.MetaproteomicAnalysis, isouter=True)
            )

        else:
            raise Exception("Unknown table")
        return _join_envo(query)


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


class ConditionSchema(BaseModel):
    op: Operation = Operation.equal
    field: str
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

    def is_column(self) -> bool:
        m = self.table.model
        if isinstance(m, AliasedClass):
            m = inspect(m).class_
        return self.field in inspect(m).all_orm_descriptors.keys()

    def compare(self):
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
            elif self.op == Operation.between:
                value = cast(Tuple[schemas.AnnotationValue, schemas.AnnotationValue], self.value)
                return and_(column >= value[0], column <= value[1])
        if self.op == Operation.between and hasattr(model, "annotations"):
            value = cast(Tuple[schemas.AnnotationValue, schemas.AnnotationValue], self.value)
            return and_(
                func.nmdc_compare(
                    model.annotations[self.field].astext, ">=", value[0]  # type: ignore
                ),
                func.nmdc_compare(
                    model.annotations[self.field].astext, "<=", value[1]  # type: ignore
                ),
            )
        if hasattr(model, "annotations"):
            json_field = model.annotations  # type: ignore
        else:
            raise InvalidAttributeException(self.table.value, self.field)
        return func.nmdc_compare(
            json_field[self.field].astext, self.op.value, self.value  # type: ignore
        )

    @property
    def key(self) -> str:
        return f"{self.table}:{self.field}"

    @classmethod
    def from_schema(cls, condition: "ConditionSchema", default_table: Table) -> "ConditionSchema":
        kwargs = condition.dict()
        if condition.field in _special_keys:
            kwargs["table"], kwargs["field"] = _special_keys[condition.field]
        elif not condition.table:
            kwargs["table"] = default_table
        return cls(**kwargs)


class BaseQuerySchema(BaseModel):
    conditions: List[ConditionSchema] = []

    @property
    def table(self) -> Table:
        raise Exception("Abstract method")

    @property
    def sorted_conditions(self) -> List[ConditionSchema]:
        conditions = [ConditionSchema.from_schema(c, self.table) for c in self.conditions]
        return sorted(conditions, key=lambda c: c.key)

    @property
    def groups(self) -> Iterator[Tuple[str, Iterator[ConditionSchema]]]:
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

    def facet(
        self,
        db: Session,
        attribute: str,
    ) -> Dict[schemas.AnnotationValue, int]:
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
