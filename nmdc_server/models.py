from typing import Type

from sqlalchemy import Column, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from nmdc_server.database import Base


ModelType = Type["AnnotatedModel"]


class AnnotatedModel:
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False, default="")

    annotations = Column(JSONB, nullable=False, default=dict)


class Study(Base, AnnotatedModel):
    __tablename__ = "study"

    gold_name = Column(String)
    gold_description = Column(String)

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
