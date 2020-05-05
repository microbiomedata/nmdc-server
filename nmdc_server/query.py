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

    def _execute(
        self, query: Query, fields: Dict[str, Tuple[models.ModelType, List[ConditionSchema]]],
    ) -> Query:
        for field, (model, conditions) in fields.items():
            query = query.filter(
                or_(*[condition.compare(model, field) for condition in conditions])
            )
        return query

    def execute(self, db: Session) -> Query:
        raise NotImplementedError()

    def _facet(
        self, db: Session, model: models.ModelType, attribute: str
    ) -> Dict[schemas.AnnotationValue, int]:
        if attribute in model.__table__.columns:
            column = getattr(model, attribute)
        else:
            column = model.annotations[attribute]  # type: ignore

        query = db.query(column, func.count(column))
        rows = query.group_by(column)
        return {value: count for value, count in rows if value is not None}

    def facet(self, db: Session, attribute: str) -> Dict[schemas.AnnotationValue, int]:
        raise NotImplementedError()


class StudyQuerySchema(BaseQuerySchema):
    def execute(self, db: Session) -> Query:
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

        query = db.query(models.Study)
        for model in joins:
            query = query.join(model)
        return self._execute(query, fields)

    def facet(self, db: Session, attribute: str) -> Dict[schemas.AnnotationValue, int]:
        return self._facet(db, models.Biosample, attribute)


class ProjectQuerySchema(BaseQuerySchema):
    def execute(self, db: Session) -> Query:
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

        query = db.query(models.Project)
        for model in joins:
            query = query.join(model)
        return self._execute(query, fields)

    def facet(self, db: Session, attribute: str) -> Dict[schemas.AnnotationValue, int]:
        return self._facet(db, models.Project, attribute)


class BiosampleQuerySchema(BaseQuerySchema):
    def execute(self, db: Session) -> Query:
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

        query = db.query(models.Biosample)
        for model in joins:
            query = query.join(model)
        return self._execute(query, fields)

    def facet(self, db: Session, attribute: str) -> Dict[schemas.AnnotationValue, int]:
        return self._facet(db, models.Biosample, attribute)


class DataObjectQuerySchema(BaseQuerySchema):
    def execute(self, db: Session) -> Query:
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

        query = db.query(models.DataObject)
        for model in joins:
            query = query.join(model)
        return self._execute(query, fields)

    def facet(self, db: Session, attribute: str) -> Dict[schemas.AnnotationValue, int]:
        return self._facet(db, models.DataObject, attribute)


class BiosampleSearchResponse(BaseModel):
    results: List[schemas.Biosample]


class SearchQuery(BaseModel):
    conditions: List[ConditionSchema]


class FacetQuery(SearchQuery):
    attribute: str


class StudySearchResponse(BaseModel):
    results: List[schemas.Study]


class ProjectSearchResponse(BaseModel):
    results: List[schemas.Project]


class DataObjectSearchResponse(BaseModel):
    results: List[schemas.DataObject]


class FacetResponse(BaseModel):
    facets: Dict[schemas.AnnotationValue, int]
