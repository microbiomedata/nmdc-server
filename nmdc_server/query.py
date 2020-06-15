from enum import Enum
from itertools import groupby
from typing import Dict, Iterator, List, Set, Tuple

from pydantic import BaseModel
from sqlalchemy import func, or_
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


class ConditionSchema(BaseModel):
    op: Operation
    field: str
    value: schemas.AnnotationValue

    def compare(self, model: models.ModelType, field_override: str = None):
        field = field_override or self.field
        if field in model.__table__.columns:
            column = getattr(model, field)
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
        return func.nmdc_compare(
            model.annotations[field].astext, self.op.value, self.value  # type: ignore
        )


class BaseQuerySchema(BaseModel):
    conditions: List[ConditionSchema]

    @property
    def sorted_conditions(self) -> List[ConditionSchema]:
        return sorted(self.conditions, key=lambda c: c.field)

    @property
    def groups(self) -> Iterator[Tuple[str, Iterator[ConditionSchema]]]:
        return groupby(self.sorted_conditions, key=lambda c: c.field)

    def parse_fields(
        self,
    ) -> Tuple[Set[models.ModelType], Dict[str, Tuple[models.ModelType, List[ConditionSchema]]]]:
        raise NotImplementedError()

    def filter_and_join(self, query: Query) -> Query:
        joins, filters = self.parse_fields()
        if models.Project in joins:
            query = query.join(models.Project)
            joins.remove(models.Project)
        for model in joins:
            query = query.join(model)
        for field, (model, conditions) in filters.items():
            query = query.filter(
                or_(*[condition.compare(model, field) for condition in conditions])
            )
        return query

    def _execute(self, query: Query,) -> Query:
        return self.filter_and_join(query).order_by("id")

    def _count(self, query: Query) -> int:
        return self.filter_and_join(query).count()

    def execute(self, db: Session) -> Query:
        raise NotImplementedError()

    def count(self, db: Session) -> int:
        raise NotImplementedError()

    def _facet(
        self, db: Session, model: models.ModelType, attribute: str,
    ) -> Dict[schemas.AnnotationValue, int]:
        if attribute in model.__table__.columns:
            column = getattr(model, attribute)
        else:
            column = model.annotations[attribute]  # type: ignore

        query = db.query(column, func.count(column))
        query = self.filter_and_join(query)
        rows = query.group_by(column)
        return {value: count for value, count in rows if value is not None}

    def facet(self, db: Session, attribute: str) -> Dict[schemas.AnnotationValue, int]:
        raise NotImplementedError()


class StudyQuerySchema(BaseQuerySchema):
    def parse_fields(
        self,
    ) -> Tuple[Set[models.ModelType], Dict[str, Tuple[models.ModelType, List[ConditionSchema]]]]:
        fields: Dict[str, Tuple[models.ModelType, List[ConditionSchema]]] = {}
        joins: Set[models.ModelType] = set()

        for field, conditions in self.groups:
            if field == "project_id":
                joins.add(models.Project)
                fields["id"] = models.Project, list(conditions)
            elif field == "sample_id":
                joins.add(models.Project)
                joins.add(models.Biosample)
                fields["id"] = models.Biosample, list(conditions)
            elif field == "data_object_id":
                joins.add(models.Project)
                joins.add(models.DataObject)
                fields["id"] = models.DataObject, list(conditions)
            else:
                fields[field] = models.Study, list(conditions)
        return joins, fields

    def execute(self, db: Session) -> Query:
        return self._execute(db.query(models.Study))

    def count(self, db: Session) -> int:
        return self._count(db.query(models.Study))

    def facet(self, db: Session, attribute: str) -> Dict[schemas.AnnotationValue, int]:
        return self._facet(db, models.Study, attribute)


class ProjectQuerySchema(BaseQuerySchema):
    def parse_fields(
        self,
    ) -> Tuple[Set[models.ModelType], Dict[str, Tuple[models.ModelType, List[ConditionSchema]]]]:
        fields: Dict[str, Tuple[models.ModelType, List[ConditionSchema]]] = {}
        joins: Set[models.ModelType] = set()

        for field, conditions in self.groups:
            if field == "sample_id":
                joins.add(models.Biosample)
                fields["id"] = models.Biosample, list(conditions)
            elif field == "data_object_id":
                joins.add(models.DataObject)
                fields["id"] = models.DataObject, list(conditions)
            else:
                fields[field] = models.Project, list(conditions)
        return joins, fields

    def execute(self, db: Session) -> Query:
        return self._execute(db.query(models.Project))

    def count(self, db: Session) -> int:
        return self._count(db.query(models.Project))

    def facet(self, db: Session, attribute: str) -> Dict[schemas.AnnotationValue, int]:
        return self._facet(db, models.Project, attribute)


class BiosampleQuerySchema(BaseQuerySchema):
    def parse_fields(
        self,
    ) -> Tuple[Set[models.ModelType], Dict[str, Tuple[models.ModelType, List[ConditionSchema]]]]:
        fields: Dict[str, Tuple[models.ModelType, List[ConditionSchema]]] = {}
        joins: Set[models.ModelType] = set()

        for field, conditions in self.groups:
            if field == "study_id":
                joins.add(models.Project)
                fields[field] = models.Project, list(conditions)
            elif field == "data_object_id":
                joins.add(models.Project)
                joins.add(models.DataObject)
                fields["id"] = models.DataObject, list(conditions)
            else:
                fields[field] = models.Biosample, list(conditions)

        return joins, fields

    def execute(self, db: Session) -> Query:
        return self._execute(db.query(models.Biosample))

    def count(self, db: Session) -> int:
        return self._count(db.query(models.Biosample))

    def facet(self, db: Session, attribute: str) -> Dict[schemas.AnnotationValue, int]:
        return self._facet(db, models.Biosample, attribute)


class DataObjectQuerySchema(BaseQuerySchema):
    def parse_fields(
        self,
    ) -> Tuple[Set[models.ModelType], Dict[str, Tuple[models.ModelType, List[ConditionSchema]]]]:
        fields: Dict[str, Tuple[models.ModelType, List[ConditionSchema]]] = {}
        joins: Set[models.ModelType] = set()

        for field, conditions in self.groups:
            if field == "study_id":
                joins.add(models.Project)
                fields[field] = models.Project, list(conditions)
            elif field == "sample_id":
                joins.add(models.Project)
                joins.add(models.Biosample)
                fields["id"] = models.Biosample, list(conditions)
            else:
                fields[field] = models.DataObject, list(conditions)
        return joins, fields

    def execute(self, db: Session) -> Query:
        return self._execute(db.query(models.DataObject))

    def count(self, db: Session) -> int:
        return self._count(db.query(models.DataObject))

    def facet(self, db: Session, attribute: str) -> Dict[schemas.AnnotationValue, int]:
        return self._facet(db, models.DataObject, attribute)


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
