from datetime import datetime
from enum import Enum
from itertools import groupby
import json
from typing import List, Set, TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy.orm import Session

from nmdc_server import models
from nmdc_server.schemas import AnnotationValue

if TYPE_CHECKING:
    from sqlalchemy_stubs.orm.query import Query


class InvalidQuery(Exception):
    pass


class Operation(Enum):
    equal = "=="
    greater = ">"
    greater_equal = ">="
    less = "<"
    less_equal = "<="


class Table(Enum):
    data_object = "data_object"
    project = "project"
    sample = "sample"
    study = "study"

    @property
    def model(self):
        return _table_to_model[self]


_table_to_model = {
    Table.data_object: models.DataObject,
    Table.project: models.Project,
    Table.sample: models.Biosample,
    Table.study: models.Study,
}


class ForeignKeys(Enum):
    data_object_id = "data_object_id"
    project_id = "project_id"
    sample_id = "sample_id"
    study_id = "study_id"

    @property
    def model(self):
        return _key_to_model[self]


_key_to_model = {
    ForeignKeys.data_object_id: models.DataObject,
    ForeignKeys.project_id: models.Project,
    ForeignKeys.sample_id: models.Biosample,
    ForeignKeys.study_id: models.Study,
}


class ConditionSchema(BaseModel):
    op: Operation
    field: str
    value: AnnotationValue

    def filter(self, table: Table):
        if self.field in ForeignKeys.__members__:
            if self.op != Operation.equal:
                raise InvalidQuery(f'Invalid foreign key operator "{self.op.name}"')

            foreign_model = ForeignKeys(self.field).model
            return foreign_model.id == self.value

        model = table.model
        value = self.value
        if isinstance(value, datetime):
            value = value.isoformat()
        json_value = json.dumps(value)
        if self.op == Operation.equal:
            return model.annotations[self.field] == json_value
        if self.op == Operation.less:
            return model.annotations[self.field] < json_value
        if self.op == Operation.less_equal:
            return model.annotations[self.field] <= json_value
        if self.op == Operation.greater:
            return model.annotations[self.field] > json_value
        if self.op == Operation.greater_equal:
            return model.annotations[self.field] >= json_value
        raise Exception("Unknown operator")


class QuerySchema(BaseModel):
    table: Table
    conditions: List[ConditionSchema]

    @property
    def sorted_conditions(self):
        return sorted(self.conditions, key=lambda c: c.field)

    @property
    def groups(self):
        return groupby(self.sorted_conditions, key=lambda c: c.field)

    def join(
        self, query: "Query", foreign_model: models.ModelType, joins: Set[models.ModelType]
    ) -> "Query":
        if foreign_model in joins:
            return
        if (
            models.Project not in joins
            and foreign_model != models.Project
            and self.table != Table.project
        ):
            joins.add(models.Project)
            query = query.join(models.Project)

        joins.add(foreign_model)
        return query.join(foreign_model)

    def execute(self, db: Session) -> "Query":
        query = db.query(self.table.model)

        joins: Set[models.ModelType] = set()
        for field, conditions in self.groups:
            # look for foreign keys and add join conditions
            if field in ForeignKeys.__members__:
                foreign_model = ForeignKeys(field).model
                query = self.join(query, foreign_model, joins)

            for condition in conditions:
                query = query.filter(condition.filter(self.table))

        return query
