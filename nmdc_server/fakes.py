from typing import Dict

from factory import Faker, SubFactory
from factory.alchemy import SQLAlchemyModelFactory
from faker.providers import lorem, python

from nmdc_server import models
from nmdc_server.database import SessionLocal
from nmdc_server.schemas import AnnotationValue

db = SessionLocal()
Faker.add_provider(lorem)
Faker.add_provider(python)


class AnnotatedFactory(SQLAlchemyModelFactory):
    id: str = Faker("pystr")
    name: str = Faker("word")
    description: str = Faker("sentence")

    annotations: Dict[str, AnnotationValue] = Faker(
        "pydict", value_types=["int", "float", "date_time", "str"]
    )


class StudyFactory(AnnotatedFactory):
    class Meta:
        model = models.Study
        sqlalchemy_session = db


class ProjectFactory(AnnotatedFactory):
    class Meta:
        model = models.Project
        sqlalchemy_session = db

    study = SubFactory(StudyFactory)


class BiosampleFactory(AnnotatedFactory):
    class Meta:
        model = models.Biosample
        sqlalchemy_session = db

    project = SubFactory(ProjectFactory)


class DataObjectFactory(AnnotatedFactory):
    class Meta:
        model = models.DataObject
        sqlalchemy_session = db

    project = SubFactory(ProjectFactory)
