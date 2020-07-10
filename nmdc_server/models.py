from typing import List, Type, Union
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship

from nmdc_server.database import Base


class EnvoTerm(Base):
    __tablename__ = "envo_term"

    id = Column(String, primary_key=True)
    label = Column(String, nullable=False)
    data = Column(JSONB, nullable=False)

    ancestor_entities = relationship(
        "EnvoTerm",
        primaryjoin="EnvoAncestor.id == EnvoTerm.id",
        secondary=lambda: EnvoAncestor.__table__,
        secondaryjoin="EnvoAncestor.ancestor_id == EnvoTerm.id",
        uselist=True,
    )
    parent_entities = relationship(
        "EnvoTerm",
        primaryjoin="EnvoAncestor.id == EnvoTerm.id",
        secondary=lambda: EnvoAncestor.__table__,
        secondaryjoin="and_(EnvoAncestor.ancestor_id == EnvoTerm.id, EnvoAncestor.direct)",
        uselist=True,
    )

    ancestors = association_proxy("ancestor_entities", "label")
    parents = association_proxy("parent_entities", "label")

    @property
    def url(self) -> str:
        return f"http://purl.obolibrary.org/obo/{self.id}"


class EnvoAncestor(Base):
    __tablename__ = "envo_ancestor"
    __table_args__ = (UniqueConstraint("id", "ancestor_id"),)

    id = Column(String, ForeignKey(EnvoTerm.id), nullable=False, primary_key=True)
    ancestor_id = Column(String, ForeignKey(EnvoTerm.id), nullable=False, primary_key=True)
    direct = Column(Boolean, nullable=False, default=lambda: False)

    term = relationship(EnvoTerm, foreign_keys=[id], lazy="joined",)
    ancestor = relationship(EnvoTerm, foreign_keys=[ancestor_id], lazy="joined")


class AnnotatedModel:
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False, default="")

    alternate_identifiers = Column(JSONB, nullable=False, default=list)
    annotations = Column(JSONB, nullable=False, default=dict)


class Study(Base, AnnotatedModel):
    __tablename__ = "study"

    add_date = Column(DateTime, nullable=False)
    mod_date = Column(DateTime, nullable=False)
    gold_name = Column(String, nullable=False, default="")
    gold_description = Column(String, nullable=False, default="")
    scientific_objective = Column(String, nullable=False, default="")

    principal_investigator_websites = relationship("StudyWebsite", cascade="all", lazy="joined")
    publication_dois = relationship("StudyPublication", cascade="all", lazy="joined")

    @property
    def open_in_gold(self):
        return f"https://gold.jgi.doe.gov/study?id={self.id}"


class Project(Base, AnnotatedModel):
    __tablename__ = "project"

    add_date = Column(DateTime, nullable=False)
    mod_date = Column(DateTime, nullable=False)
    study_id = Column(String, ForeignKey("study.id"), nullable=False)
    study = relationship("Study", backref="projects")

    @property
    def open_in_gold(self):
        return f"https://gold.jgi.doe.gov/project?id={self.id}"


class Biosample(Base, AnnotatedModel):
    __tablename__ = "biosample"

    add_date = Column(DateTime, nullable=False)
    mod_date = Column(DateTime, nullable=False)
    depth = Column(Float, nullable=True)
    env_broad_scale_id = Column(String, ForeignKey(EnvoTerm.id), nullable=True)
    env_local_scale_id = Column(String, ForeignKey(EnvoTerm.id), nullable=True)
    env_medium_id = Column(String, ForeignKey(EnvoTerm.id), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    project_id = Column(String, ForeignKey("project.id"), nullable=False)
    project = relationship("Project", backref="biosamples")

    env_broad_scale = relationship(EnvoTerm, foreign_keys=[env_broad_scale_id], lazy="joined")
    env_local_scale = relationship(EnvoTerm, foreign_keys=[env_local_scale_id], lazy="joined")
    env_medium = relationship(EnvoTerm, foreign_keys=[env_medium_id], lazy="joined")

    @property
    def env_broad_scale_terms(self) -> List[str]:
        return list(self.env_broad_scale.ancestors)

    @property
    def env_local_scale_terms(self) -> List[str]:
        return list(self.env_local_scale.ancestors)

    @property
    def env_medium_terms(self) -> List[str]:
        return list(self.env_medium.ancestors)

    @property
    def open_in_gold(self):
        return f"https://gold.jgi.doe.gov/biosample?id={self.id}"


class DataObject(Base, AnnotatedModel):
    __tablename__ = "data_object"

    project_id = Column(String, ForeignKey("project.id"), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
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
