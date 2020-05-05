from typing import Type, Union
from uuid import uuid4

from sqlalchemy import Column, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from nmdc_server.database import Base


class AnnotatedModel:
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False, default="")

    annotations = Column(JSONB, nullable=False, default=dict)


class Study(Base, AnnotatedModel):
    __tablename__ = "study"

    gold_name = Column(String)
    gold_description = Column(String)
    scientific_objective = Column(String)

    principal_investigator_websites = relationship("StudyWebsite", cascade="all", lazy="joined")
    publication_dois = relationship("StudyPublication", cascade="all", lazy="joined")

    @property
    def open_in_gold(self):
        return f"https://gold.jgi.doe.gov/study?id={self.id}"


class Project(Base, AnnotatedModel):
    __tablename__ = "project"

    study_id = Column(String, ForeignKey("study.id"), nullable=False)
    study = relationship("Study", backref="projects")

    @property
    def open_in_gold(self):
        return f"https://gold.jgi.doe.gov/project?id={self.id}"


class Biosample(Base, AnnotatedModel):
    __tablename__ = "biosample"

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    project_id = Column(String, ForeignKey("project.id"), nullable=False)
    project = relationship("Project", backref="biosamples")

    @property
    def open_in_gold(self):
        return f"https://gold.jgi.doe.gov/biosample?id={self.id}"


class DataObject(Base, AnnotatedModel):
    __tablename__ = "data_object"

    project_id = Column(String, ForeignKey("project.id"), nullable=False)
    project = relationship("Project", backref="data_objects")


ModelType = Union[Type[Study], Type[Project], Type[Biosample], Type[DataObject]]


class Website(Base):
    __tablename__ = "website"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    url = Column(String, nullable=False, unique=True)


class StudyWebsite(Base):
    __tablename__ = "study_website"

    study_id = Column(String, ForeignKey("study.id"), primary_key=True)
    website_id = Column(UUID(as_uuid=True), ForeignKey("website.id"), primary_key=True)

    website = relationship(Website, cascade="all")


class Publication(Base):
    __tablename__ = "publication"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    doi = Column(String, nullable=False, unique=True)


class StudyPublication(Base):
    __tablename__ = "study_publication"

    study_id = Column(String, ForeignKey("study.id"), primary_key=True)
    publication_id = Column(UUID(as_uuid=True), ForeignKey("publication.id"), primary_key=True)

    publication = relationship(Publication, cascade="all")
