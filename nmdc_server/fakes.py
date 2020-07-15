from collections import OrderedDict
from typing import Dict
from uuid import uuid4

from factory import Faker, post_generation, SubFactory
from factory.alchemy import SQLAlchemyModelFactory
from faker.providers import BaseProvider, date_time, geo, internet, lorem, misc, python
from sqlalchemy.orm.scoping import scoped_session

from nmdc_server import models
from nmdc_server.database import SessionLocal
from nmdc_server.schemas import AnnotationValue


class DoiProvider(BaseProvider):
    def doi(self):
        num = self.random_int(min=1000, max=999999999)
        post_size = self.random_int(min=1, max=10)
        post = self.bothify("?" * post_size).lower()
        return f"10.{num}/{post}"

    def uuid(self):
        return uuid4()


db = scoped_session(SessionLocal)
Faker.add_provider(DoiProvider)
Faker.add_provider(date_time)
Faker.add_provider(geo)
Faker.add_provider(internet)
Faker.add_provider(lorem)
Faker.add_provider(misc)
Faker.add_provider(python)


class AnnotatedFactory(SQLAlchemyModelFactory):
    id: str = Faker("pystr")
    name: str = Faker("word")
    description: str = Faker("sentence")

    alternate_identifiers = Faker("pylist", nb_elements=2, value_types=[str])
    annotations: Dict[str, AnnotationValue] = Faker(
        "pydict", value_types=["int", "float", "date_time", "str"]
    )


class WebsiteFactory(SQLAlchemyModelFactory):
    id = Faker("uuid")
    url = Faker("uri")

    class Meta:
        model = models.Website
        sqlalchemy_session = db


class PublicationFactory(SQLAlchemyModelFactory):
    id = Faker("uuid")
    doi = Faker("doi")

    class Meta:
        model = models.Publication
        sqlalchemy_session = db


class EnvoTermFactory(SQLAlchemyModelFactory):
    id = Faker("pystr")
    label = Faker("word")
    data = Faker("pydict", value_types=["str"])

    class Meta:
        model = models.EnvoTerm
        sqlalchemy_session = db

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        term = models.EnvoTerm(*args, **kwargs)
        db.add(models.EnvoAncestor(term=term, ancestor=term, direct=False))
        return term


class EnvoAncestorFactory(SQLAlchemyModelFactory):
    term = SubFactory(EnvoTermFactory)
    ancestor = SubFactory(EnvoTermFactory)
    direct = Faker("random_element", elements=OrderedDict([(True, 0.1), (False, 0.9)]))

    class Meta:
        model = models.EnvoAncestor
        sqlalchemy_session = db


class StudyFactory(AnnotatedFactory):
    add_date = Faker("date_time")
    mod_date = Faker("date_time")
    gold_name = Faker("word")
    gold_description = Faker("sentence")
    scientific_objective = Faker("sentence")

    class Meta:
        model = models.Study
        sqlalchemy_session = db

    @post_generation
    def principal_investigator_websites(self, create, extracted, **kwargs):
        if not create:
            return

        if not extracted:
            extracted = [StudyWebsiteFactory(), StudyWebsiteFactory()]

        for website in extracted:
            self.principal_investigator_websites.append(website)

    @post_generation
    def publication_dois(self, create, extracted, **kwargs):
        if not create:
            return

        if not extracted:
            extracted = [StudyPublicationFactory(), StudyPublicationFactory()]

        for publication in extracted:
            self.publication_dois.append(publication)


class StudyWebsiteFactory(SQLAlchemyModelFactory):
    website = SubFactory(WebsiteFactory)

    class Meta:
        model = models.StudyWebsite
        sqlalchemy_session = db


class StudyPublicationFactory(SQLAlchemyModelFactory):
    publication = SubFactory(PublicationFactory)

    class Meta:
        model = models.StudyPublication
        sqlalchemy_session = db


class ProjectFactory(AnnotatedFactory):
    class Meta:
        model = models.Project
        sqlalchemy_session = db

    add_date = Faker("date_time")
    mod_date = Faker("date_time")
    study = SubFactory(StudyFactory)


class BiosampleFactory(AnnotatedFactory):
    class Meta:
        model = models.Biosample
        sqlalchemy_session = db

    add_date = Faker("date_time")
    mod_date = Faker("date_time")
    depth = Faker("random_number", digits=3)
    env_broad_scale = SubFactory(EnvoTermFactory)
    env_local_scale = SubFactory(EnvoTermFactory)
    env_medium = SubFactory(EnvoTermFactory)
    latitude = Faker("latitude")
    longitude = Faker("longitude")
    project = SubFactory(ProjectFactory)


class DataObjectFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.DataObject
        sqlalchemy_session = db

    id: str = Faker("pystr")
    name: str = Faker("word")
    description: str = Faker("sentence")
    file_size_bytes = Faker("pyint")
    md5_checksum = Faker("md5", raw_output=False)
    project = SubFactory(ProjectFactory)
