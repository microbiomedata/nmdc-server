from enum import Enum
from itertools import groupby
from typing import cast, Dict, Iterator, List, Optional, Tuple, Union

from pydantic import BaseModel, validator
from sqlalchemy import and_, distinct, func, or_
from sqlalchemy.orm import Query, Session

from nmdc_server import models, schemas


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

    @property
    def model(self) -> models.ModelType:
        if self == Table.biosample:
            return models.Biosample
        elif self == Table.study:
            return models.Study
        elif self == Table.project:
            return models.Project
        elif self == Table.data_object:
            return models.Project
        raise Exception("Unknown table")

    def query(self, db: Session) -> Query:
        if self == Table.biosample:
            return (
                db.query(distinct(models.Biosample.id).label("id"))
                .join(models.Project)
                .join(models.DataObject, isouter=True)
                .join(models.Study)
            )
        elif self == Table.study:
            return (
                db.query(distinct(models.Study.id).label("id"))
                .join(models.Project, isouter=True)
                .join(models.Biosample, isouter=True)
                .join(models.DataObject, isouter=True)
            )
        elif self == Table.project:
            return (
                db.query(distinct(models.Project.id).label("id"))
                .join(models.Study)
                .join(models.Biosample, isouter=True)
                .join(models.DataObject, isouter=True)
            )
        elif self == Table.data_object:
            return (
                db.query(distinct(models.DataObject.id).label("id"))
                .join(models.Project)
                .join(models.Biosample, isouter=True)
                .join(models.Study)
            )
        raise Exception("Unknown table")


_foreign_keys: Dict[str, Table] = {
    "study_id": Table.study,
    "sample_id": Table.biosample,
    "project_id": Table.project,
    "data_object_id": Table.data_object,
}


class ConditionSchema(BaseModel):
    op: Operation = Operation.equal
    field: str
    value: Union[schemas.AnnotationValue, Tuple[float, float]]
    table: Optional[Table]

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


class Condition(ConditionSchema):
    table: Table

    def compare(self):
        model = self.table.model
        if self.field in model.__table__.columns:
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
                value = cast(Tuple[float, float], self.value)
                return and_(column >= value[0], column <= value[1])
        if self.op == Operation.between:
            value = cast(Tuple[float, float], self.value)
            return and_(
                func.nmdc_compare(
                    model.annotations[self.field].astext, ">=", value[0]  # type: ignore
                ),
                func.nmdc_compare(
                    model.annotations[self.field].astext, "<=", value[1]  # type: ignore
                ),
            )
        return func.nmdc_compare(
            model.annotations[self.field].astext, self.op.value, self.value  # type: ignore
        )

    @property
    def key(self) -> str:
        return f"{self.table}:{self.field}"

    @classmethod
    def from_schema(cls, condition: ConditionSchema, default_table: Table) -> "Condition":
        kwargs = condition.dict()
        if not condition.table:
            if condition.field in _foreign_keys:
                kwargs["table"] = _foreign_keys[condition.field]
                kwargs["field"] = "id"
            else:
                kwargs["table"] = default_table
        return cls(**kwargs)


class BaseQuerySchema(BaseModel):
    conditions: List[ConditionSchema]

    @property
    def table(self) -> Table:
        raise Exception("Abstract method")

    @property
    def sorted_conditions(self) -> List[Condition]:
        conditions = [Condition.from_schema(c, self.table) for c in self.conditions]
        return sorted(conditions, key=lambda c: c.key)

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

    def facet(self, db: Session, attribute: str,) -> Dict[schemas.AnnotationValue, int]:
        model = self.table.model
        if attribute in model.__table__.columns:
            column = getattr(model, attribute)
        else:
            column = model.annotations[attribute]  # type: ignore

        subquery = self.query(db).subquery()
        query = db.query(column, func.count(column)).join(subquery, model.id == subquery.c.id)
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


class DataObjectQuerySchema(BaseQuerySchema):
    @property
    def table(self) -> Table:
        return Table.data_object


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


class FacetResponse(BaseModel):
    facets: Dict[schemas.AnnotationValue, int]
