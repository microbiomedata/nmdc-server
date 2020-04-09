from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from nmdc_server.database import Base


class AnnotatedModel:
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False, default="")

    annotations = Column(JSONB, nullable=False, default=dict)


class Study(Base, AnnotatedModel):
    __tablename__ = "study"


class Project(Base, AnnotatedModel):
    __tablename__ = "project"

    study_id = Column(String, ForeignKey("study.id"), nullable=False)
    study = relationship("Study")


class Biosample(Base, AnnotatedModel):
    __tablename__ = "biosample"

    project_id = Column(String, ForeignKey("project.id"), nullable=False)
    project = relationship("Project")


class DataObject(Base, AnnotatedModel):
    __tablename__ = "data_object"

    project_id = Column(String, ForeignKey("project.id"), nullable=False)
    project = relationship("Project")
