import enum
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional, Type, Union
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Session, backref, query_expression, relationship
from sqlalchemy.orm.relationships import RelationshipProperty

from nmdc_server.database import Base, update_multiomics_sql

# The models in the file are a specialized representation of the domain objects
# described by https://microbiomedata.github.io/nmdc-schema/.


def gold_url(base: str, id: str, gold_identifiers: Optional[list[str]] = None) -> Optional[str]:
    if id.startswith("gold:"):
        return f"{base}{id[5:]}"
    if gold_identifiers and gold_identifiers[0].lower().startswith("gold:"):
        return f"{base}{gold_identifiers[0][5:]}"
    return None


# Many tables have "inputs" and "outputs" attributes that are many-to-many
# relationships with a data_object.  These functions generate the sqlalchemy
# constructs for these relationships in a consistent way.
def input_association(table: str) -> Table:
    """Generate a many-to-many relationship with data_objects for inputs."""
    return Table(
        f"{table}_input_association",
        Base.metadata,
        Column(f"{table}_id", String, ForeignKey(f"{table}.id")),
        Column("data_object_id", String, ForeignKey("data_object.id")),
        UniqueConstraint(f"{table}_id", "data_object_id"),
    )


def input_relationship(association: Table) -> "RelationshipProperty[DataObject]":
    return relationship(
        "DataObject",
        secondary=association,
    )


def output_association(table: str) -> Table:
    """Generate a many-to-many relationship with data_objects for outputs."""
    return Table(
        f"{table}_output_association",
        Base.metadata,
        Column(f"{table}_id", String, ForeignKey(f"{table}.id")),
        Column("data_object_id", String, ForeignKey("data_object.id")),
        UniqueConstraint(f"{table}_id", "data_object_id"),
    )


def output_relationship(association: Table) -> "RelationshipProperty[DataObject]":
    return relationship(
        "DataObject",
        secondary=association,
    )


# Store ENVO related data loaded from http://www.obofoundry.org/ontology/envo.html
class EnvoTerm(Base):
    __tablename__ = "envo_term"

    id = Column(String, primary_key=True)
    label = Column(String, nullable=False)
    data = Column(JSONB, nullable=False)

    # stubs don't yet know about "overlaps"
    ancestor_entities = relationship(  # type: ignore
        "EnvoTerm",
        primaryjoin="EnvoAncestor.id == EnvoTerm.id",
        secondary=lambda: EnvoAncestor.__table__,
        secondaryjoin="EnvoAncestor.ancestor_id == EnvoTerm.id",
        uselist=True,
        overlaps="parent_entities, id",
        viewonly=True,
    )
    parent_entities = relationship(  # type: ignore
        "EnvoTerm",
        primaryjoin="EnvoAncestor.id == EnvoTerm.id",
        secondary=lambda: EnvoAncestor.__table__,
        secondaryjoin="and_(EnvoAncestor.ancestor_id == EnvoTerm.id, EnvoAncestor.direct)",
        uselist=True,
        overlaps="ancestor_entities, id",
        viewonly=True,
    )

    ancestors = association_proxy("ancestor_entities", "label")
    parents = association_proxy("parent_entities", "label")

    @property
    def url(self) -> str:
        return f"http://purl.obolibrary.org/obo/{self.id}"


# This table stores denormalized envo hierarchy information so that we can
# query all ancestor terms with a recursive query.
class EnvoAncestor(Base):
    __tablename__ = "envo_ancestor"
    __table_args__ = (UniqueConstraint("id", "ancestor_id"),)

    id = Column(String, ForeignKey(EnvoTerm.id), nullable=False, primary_key=True)
    ancestor_id = Column(String, ForeignKey(EnvoTerm.id), nullable=False, primary_key=True)

    # denotes that the ancestor is a direct parent of the linked term
    direct = Column(Boolean, nullable=False, default=lambda: False)

    term = relationship(
        EnvoTerm,
        foreign_keys=[id],
        lazy="joined",
    )
    ancestor = relationship(EnvoTerm, foreign_keys=[ancestor_id], lazy="joined")


class KoTermToModule(Base):
    __tablename__ = "ko_term_to_module"

    term = Column(String, nullable=False, primary_key=True)
    module = Column(String, nullable=False, primary_key=True, index=True)


class KoTermToPathway(Base):
    __tablename__ = "ko_term_to_pathway"

    term = Column(String, nullable=False, primary_key=True)
    pathway = Column(String, nullable=False, primary_key=True, index=True)


class CogTermToPathway(Base):
    __tablename__ = "cog_term_to_pathway"

    term = Column(String, nullable=False, primary_key=True)
    pathway = Column(String, nullable=False, primary_key=True, index=True)


class CogTermToFunction(Base):
    __tablename__ = "cog_term_to_function"

    term = Column(String, nullable=False, primary_key=True)
    function = Column(String, nullable=False, primary_key=True, index=True)


class PfamEntryToClan(Base):
    __tablename__ = "pfam_entry_to_clan"

    entry = Column(String, nullable=False, primary_key=True)
    clan = Column(String, nullable=False, primary_key=True, index=True)


class GoTermToPfamEntry(Base):
    __tablename__ = "go_term_to_pfam_entry"

    term = Column(String, nullable=False, primary_key=True)
    entry = Column(String, nullable=False, primary_key=True, index=True)


class KoTermText(Base):
    __tablename__ = "ko_term_text"

    term = Column(String, nullable=False, primary_key=True)
    text = Column(Text, nullable=False)


class PfamTermText(Base):
    __tablename__ = "pfam_term_text"

    term = Column(String, nullable=False, primary_key=True)
    text = Column(Text, nullable=False)


class CogTermText(Base):
    __tablename__ = "cog_term_text"

    term = Column(String, nullable=False, primary_key=True)
    text = Column(Text, nullable=False)


class GoTermText(Base):
    __tablename__ = "go_term_text"

    term = Column(String, nullable=False, primary_key=True)
    text = Column(Text, nullable=False)


class SearchIndex(Base):
    __tablename__ = "search_index"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Condition value (only == operator supported)
    table = Column(String, nullable=False)
    value = Column(String, nullable=False)
    field = Column(String, nullable=False)
    count = Column(Integer, nullable=False)


class PrincipalInvestigator(Base):
    __tablename__ = "principal_investigator"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    orcid = Column(String, nullable=True)

    # a PI profile image... originally we didn't have a place to store static content
    # so the image data is placed in the database.
    image = Column(LargeBinary, nullable=True)


class DOIType(enum.Enum):
    AWARD = "award_doi"
    DATASET = "dataset_doi"
    PUBLICATION = "publication_doi"


study_doi_association = Table(
    "study_doi_association",
    Base.metadata,
    Column("study_id", ForeignKey("study.id"), primary_key=True),
    Column("doi_id", ForeignKey("doi_info.id"), primary_key=True),
)


# Caches information from doi.org
class DOIInfo(Base):
    __tablename__ = "doi_info"

    id = Column(
        String,
        CheckConstraint(r"id ~* '^10.\d{4,9}/[-._;()/:a-zA-Z0-9]+$'", name="ck_doi_format"),
        primary_key=True,
    )
    info = Column(JSONB, nullable=False, default=dict)
    doi_type = Column(Enum(DOIType))
    studies = relationship("Study", secondary=study_doi_association, back_populates="dois")
    doi_provider = Column(String, nullable=True)


class AnnotatedModel:
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False, default="")

    alternate_identifiers = Column(JSONB, nullable=False, default=list)
    annotations = Column(JSONB, nullable=False, default=dict)


class Study(Base, AnnotatedModel):
    __tablename__ = "study"

    add_date = Column(DateTime, nullable=True)
    mod_date = Column(DateTime, nullable=True)
    gold_name = Column(String, nullable=False, default="")
    gold_description = Column(String, nullable=False, default="")
    scientific_objective = Column(String, nullable=False, default="")
    dois = relationship("DOIInfo", secondary=study_doi_association, back_populates="studies")
    multiomics = Column(Integer, nullable=False, default=0)

    # TODO migrate these into relations or something
    has_credit_associations = Column(JSONB, nullable=True)
    relevant_protocols = Column(JSONB, nullable=True)
    funding_sources = Column(JSONB, nullable=True)
    gold_study_identifiers = Column(JSONB, nullable=True)

    study_category = Column(String, nullable=True)
    homepage_website = Column(JSONB, nullable=True)
    part_of = Column(JSONB, nullable=True)
    children = Column(JSONB, nullable=True)

    # These query expressions are a way to inject additional aggregation information
    # into the query at search time.  See `with_expression` usage in `query.py`.
    # TODO: Specify a default expression so that sample counts are present in
    #       non-search responses.
    sample_count = query_expression()
    omics_counts = query_expression()
    omics_processing_counts = query_expression()

    principal_investigator_id = Column(
        UUID(as_uuid=True), ForeignKey("principal_investigator.id"), nullable=True
    )
    principal_investigator = relationship("PrincipalInvestigator", cascade="all")
    principal_investigator_name = association_proxy("principal_investigator", "name")
    image = Column(LargeBinary, nullable=True)

    @property
    def principal_investigator_image_url(self):
        if self.principal_investigator_id is not None:
            return f"/api/principal_investigator/{self.principal_investigator_id}"
        return ""

    @property
    def image_url(self):
        if self.image:
            return f"/api/study/{self.id}/image"
        return ""

    principal_investigator_websites = relationship("StudyWebsite", cascade="all", lazy="joined")

    @property
    def open_in_gold(self) -> Optional[str]:
        return gold_url(
            "https://gold.jgi.doe.gov/study?id=",
            self.id,
            self.gold_study_identifiers,  # type: ignore
        )

    @property
    def doi_map(self) -> Dict[str, Any]:
        doi_info = dict()
        for doi in self.dois:  # type: ignore
            doi_info[doi.id] = {
                "info": doi.info,
                "category": doi.doi_type,
                "provider": doi.doi_provider,
            }
        return doi_info


biosample_input_association = Table(
    "biosample_input_association",
    Base.metadata,
    Column("omics_processing_id", ForeignKey("omics_processing.id"), primary_key=True),
    Column("biosample_id", ForeignKey("biosample.id"), primary_key=True),
)


class Biosample(Base, AnnotatedModel):
    __tablename__ = "biosample"

    add_date = Column(DateTime, nullable=True)
    mod_date = Column(DateTime, nullable=True)
    collection_date = Column(DateTime, nullable=True)
    depth = Column(Float, nullable=True)
    env_broad_scale_id = Column(String, ForeignKey(EnvoTerm.id), nullable=True)
    env_local_scale_id = Column(String, ForeignKey(EnvoTerm.id), nullable=True)
    env_medium_id = Column(String, ForeignKey(EnvoTerm.id), nullable=True)

    # These columns can be null to accomodate legacy data, but all new data will have lat/lon
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    study_id = Column(String, ForeignKey("study.id"), nullable=False)
    multiomics = Column(Integer, nullable=False, default=0)
    emsl_biosample_identifiers = Column(JSONB, nullable=True)
    omics_processing = relationship(
        "OmicsProcessing", secondary=biosample_input_association, back_populates="biosample_inputs"
    )

    # gold terms
    ecosystem = Column(String, nullable=True)
    ecosystem_category = Column(String, nullable=True)
    ecosystem_type = Column(String, nullable=True)
    ecosystem_subtype = Column(String, nullable=True)
    specific_ecosystem = Column(String, nullable=True)

    study = relationship(Study, backref="biosamples")
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
    def open_in_gold(self) -> Optional[str]:
        return gold_url("https://gold.jgi.doe.gov/biosample?id=", self.id)

    # Multiomics bit strings are denormalized information representing which
    # omics types exist for each sample.  This information is updated from a
    # sql query after ingestion.
    @classmethod
    def populate_multiomics(cls, db: Session):
        db.execute(update_multiomics_sql)
        db.commit()


omics_processing_output_association = output_association("omics_processing")


class OmicsProcessing(Base, AnnotatedModel):
    __tablename__ = "omics_processing"

    add_date = Column(DateTime, nullable=True)
    mod_date = Column(DateTime, nullable=True)
    biosample_inputs = relationship(
        "Biosample", secondary=biosample_input_association, back_populates="omics_processing"
    )
    study_id = Column(String, ForeignKey("study.id"), nullable=True)
    study = relationship("Study", backref="omics_processing")

    outputs = output_relationship(omics_processing_output_association)
    has_outputs = association_proxy("outputs", "id")

    @property
    def open_in_gold(self) -> Optional[str]:
        return gold_url("https://gold.jgi.doe.gov/project?id=", self.id)

    # This property injects information in the omics_processing result
    # regarding output data from workflow processing runs.  Because there
    # are no filters that filter out individual processing runs, this
    # can be done outside of the main query.  For this reason, it does
    # not have to be added as a `query_expression`.
    @property
    def omics_data(self) -> Iterator["PipelineStep"]:
        for model in workflow_activity_types:
            name = model.__tablename__  # type: ignore
            for pipeline in getattr(self, name):
                yield pipeline


class DataObject(Base):
    __tablename__ = "data_object"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False, default="")
    file_size_bytes = Column(BigInteger, nullable=True)
    md5_checksum = Column(String, nullable=True)
    url = Column(String, nullable=True)
    file_type = Column(String, nullable=True)
    file_type_description = Column(String, nullable=True)

    # denormalized relationship with a workflow activity output
    workflow_type = Column(String, nullable=True)

    # denormalized relationship representing the source omics_processing
    omics_processing_id = Column(String, ForeignKey("omics_processing.id"), nullable=True)
    omics_processing = relationship(OmicsProcessing)

    @hybrid_property
    def downloads(self) -> int:
        # TODO: This can probably be done with a more efficient aggregation
        return len(self.download_entities) + len(self.bulk_download_entities)  # type: ignore


# This is a base class for all workflow processing activities.
# https://microbiomedata.github.io/nmdc-schema/WorkflowExecutionActivity.html
class PipelineStep:
    __tablename__ = "base_pipeline_step"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    git_url = Column(String, nullable=False)
    started_at_time = Column(DateTime, nullable=False)
    ended_at_time = Column(DateTime, nullable=False)
    execution_resource = Column(String, nullable=False)

    @declared_attr
    def omics_processing_id(cls):
        return Column(String, ForeignKey("omics_processing.id"), nullable=False)

    @declared_attr
    def omics_processing(cls):
        return relationship("OmicsProcessing", backref=backref(cls.__tablename__, lazy="joined"))

    has_inputs = association_proxy("inputs", "id")
    has_outputs = association_proxy("outputs", "id")


reads_qc_input_association = input_association("reads_qc")
reads_qc_output_association = output_association("reads_qc")


class ReadsQC(Base, PipelineStep):
    __tablename__ = "reads_qc"

    input_read_count = Column(BigInteger, nullable=True)
    input_read_bases = Column(BigInteger, nullable=True)
    output_read_count = Column(BigInteger, nullable=True)
    output_read_bases = Column(BigInteger, nullable=True)

    inputs = input_relationship(reads_qc_input_association)
    outputs = output_relationship(reads_qc_output_association)


metagenome_assembly_input_association = input_association("metagenome_assembly")
metagenome_assembly_output_association = output_association("metagenome_assembly")


class MetagenomeAssembly(Base, PipelineStep):
    __tablename__ = "metagenome_assembly"

    scaffolds = Column(Float, nullable=True)
    contigs = Column(Float, nullable=True)
    scaf_bp = Column(Float, nullable=True)
    contig_bp = Column(Float, nullable=True)
    scaf_n50 = Column(Float, nullable=True)
    scaf_l50 = Column(Float, nullable=True)
    ctg_n50 = Column(Float, nullable=True)
    ctg_l50 = Column(Float, nullable=True)
    scaf_n90 = Column(Float, nullable=True)
    scaf_l90 = Column(Float, nullable=True)
    ctg_n90 = Column(Float, nullable=True)
    ctg_l90 = Column(Float, nullable=True)
    scaf_max = Column(Float, nullable=True)
    ctg_max = Column(Float, nullable=True)
    scaf_n_gt50k = Column(Float, nullable=True)
    scaf_l_gt50k = Column(Float, nullable=True)
    scaf_pct_gt50k = Column(Float, nullable=True)
    num_input_reads = Column(Float, nullable=True)
    num_aligned_reads = Column(Float, nullable=True)

    scaf_logsum = Column(Float, nullable=True)
    scaf_powsum = Column(Float, nullable=True)
    ctg_logsum = Column(Float, nullable=True)
    ctg_powsum = Column(Float, nullable=True)
    asm_score = Column(Float, nullable=True)
    gap_pct = Column(Float, nullable=True)
    gc_avg = Column(Float, nullable=True)
    gc_std = Column(Float, nullable=True)

    inputs = input_relationship(metagenome_assembly_input_association)
    outputs = output_relationship(metagenome_assembly_output_association)


metatranscriptome_assembly_input_association = input_association("metatranscriptome_assembly")
metatranscriptome_assembly_output_association = output_association("metatranscriptome_assembly")


class MetatranscriptomeAssembly(Base, PipelineStep):
    __tablename__ = "metatranscriptome_assembly"

    scaffolds = Column(Float, nullable=True)
    contigs = Column(Float, nullable=True)
    scaf_bp = Column(Float, nullable=True)
    contig_bp = Column(Float, nullable=True)
    scaf_n50 = Column(Float, nullable=True)
    scaf_l50 = Column(Float, nullable=True)
    ctg_n50 = Column(Float, nullable=True)
    ctg_l50 = Column(Float, nullable=True)
    scaf_n90 = Column(Float, nullable=True)
    scaf_l90 = Column(Float, nullable=True)
    ctg_n90 = Column(Float, nullable=True)
    ctg_l90 = Column(Float, nullable=True)
    scaf_max = Column(Float, nullable=True)
    ctg_max = Column(Float, nullable=True)
    scaf_n_gt50k = Column(Float, nullable=True)
    scaf_l_gt50k = Column(Float, nullable=True)
    scaf_pct_gt50k = Column(Float, nullable=True)
    num_input_reads = Column(Float, nullable=True)
    num_aligned_reads = Column(Float, nullable=True)

    scaf_logsum = Column(Float, nullable=True)
    scaf_powsum = Column(Float, nullable=True)
    ctg_logsum = Column(Float, nullable=True)
    ctg_powsum = Column(Float, nullable=True)
    asm_score = Column(Float, nullable=True)
    gap_pct = Column(Float, nullable=True)
    gc_avg = Column(Float, nullable=True)
    gc_std = Column(Float, nullable=True)

    inputs = input_relationship(metatranscriptome_assembly_input_association)
    outputs = output_relationship(metatranscriptome_assembly_output_association)


metagenome_annotation_input_association = input_association("metagenome_annotation")
metagenome_annotation_output_association = output_association("metagenome_annotation")


class MetagenomeAnnotation(Base, PipelineStep):
    __tablename__ = "metagenome_annotation"

    inputs = input_relationship(metagenome_annotation_input_association)
    outputs = output_relationship(metagenome_annotation_output_association)


metatranscriptome_annotation_input_association = input_association("metatranscriptome_annotation")
metatranscriptome_annotation_output_association = output_association("metatranscriptome_annotation")


class MetatranscriptomeAnnotation(Base, PipelineStep):
    __tablename__ = "metatranscriptome_annotation"

    inputs = input_relationship(metatranscriptome_annotation_input_association)
    outputs = output_relationship(metatranscriptome_annotation_output_association)


metaproteomic_analysis_input_association = input_association("metaproteomic_analysis")
metaproteomic_analysis_output_association = output_association("metaproteomic_analysis")


class MetaproteomicAnalysis(Base, PipelineStep):
    __tablename__ = "metaproteomic_analysis"

    inputs = input_relationship(metaproteomic_analysis_input_association)
    outputs = output_relationship(metaproteomic_analysis_output_association)


mags_analysis_input_association = input_association("mags_analysis")
mags_analysis_output_association = output_association("mags_analysis")


class MAGsAnalysis(Base, PipelineStep):
    __tablename__ = "mags_analysis"

    input_contig_num = Column(BigInteger)
    too_short_contig_num = Column(BigInteger)
    low_depth_contig_num = Column(BigInteger)
    unbinned_contig_num = Column(BigInteger)
    binned_contig_num = Column(BigInteger)

    inputs = input_relationship(mags_analysis_input_association)
    outputs = output_relationship(mags_analysis_output_association)


class MAG(Base):
    __tablename__ = "mag"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    mags_analysis_id = Column(String, ForeignKey("mags_analysis.id"), nullable=False)
    bin_name = Column(String, nullable=True)
    number_of_contig = Column(BigInteger, nullable=True)
    completeness = Column(Float, nullable=True)
    contamination = Column(Float, nullable=True)
    gene_count = Column(BigInteger, nullable=True)
    bin_quality = Column(String, nullable=True)
    num_16s = Column(BigInteger, nullable=True)
    num_5s = Column(BigInteger, nullable=True)
    num_23s = Column(BigInteger, nullable=True)
    num_t_rna = Column(BigInteger, nullable=True)

    mags_analysis = relationship(MAGsAnalysis, backref="mags_list")


nom_analysis_input_association = input_association("nom_analysis")
nom_analysis_output_association = output_association("nom_analysis")


class NOMAnalysis(Base, PipelineStep):
    __tablename__ = "nom_analysis"

    used = Column(String, nullable=False)

    inputs = input_relationship(nom_analysis_input_association)
    outputs = output_relationship(nom_analysis_output_association)


read_based_analysis_input_association = input_association("read_based_analysis")
read_based_analysis_output_association = output_association("read_based_analysis")


class ReadBasedAnalysis(Base, PipelineStep):
    __tablename__ = "read_based_analysis"

    inputs = input_relationship(read_based_analysis_input_association)
    outputs = output_relationship(read_based_analysis_output_association)


metatranscriptome_input_association = input_association("metatranscriptome")
metatranscriptome_output_association = output_association("metatranscriptome")


class Metatranscriptome(Base, PipelineStep):
    """Corresponds to the metatranscriptome_expression_analysis_set"""

    __tablename__ = "metatranscriptome"

    inputs = input_relationship(metatranscriptome_input_association)
    outputs = output_relationship(metatranscriptome_output_association)


metabolomics_analysis_input_association = input_association("metabolomics_analysis")
metabolomics_analysis_output_association = output_association("metabolomics_analysis")


class MetabolomicsAnalysis(Base, PipelineStep):
    __tablename__ = "metabolomics_analysis"

    used = Column(String, nullable=False)

    inputs = input_relationship(metabolomics_analysis_input_association)
    outputs = output_relationship(metabolomics_analysis_output_association)


class Website(Base):
    __tablename__ = "website"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    url = Column(String, nullable=False, unique=True)


class StudyWebsite(Base):
    __tablename__ = "study_website"

    study_id = Column(String, ForeignKey("study.id"), primary_key=True)
    website_id = Column(UUID(as_uuid=True), ForeignKey("website.id"), primary_key=True)

    website = relationship(Website, cascade="all")


# This table contains KO terms detected in metagenome and metaproteomic workflow
# activities
class GeneFunction(Base):
    __tablename__ = "gene_function"

    id = Column(String, primary_key=True)


# Store references to individual downloads to provide download statistics information.
class FileDownload(Base):
    __tablename__ = "file_download"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    created = Column(DateTime, nullable=False, default=datetime.utcnow)
    data_object_id = Column(String, ForeignKey("data_object.id"), nullable=False)
    ip = Column(String, nullable=False)
    user_agent = Column(String, nullable=True)
    orcid = Column(String, nullable=False)

    data_object = relationship(DataObject, backref="download_entities")


# This is a basic mutex lock to ensure only 1 ingest job is queued at a time.
class IngestLock(Base):
    __tablename__ = "ingest_lock"
    __table_args__ = (CheckConstraint("id", name="singleton"),)

    id = Column(Boolean, primary_key=True, default=True)
    started = Column(DateTime, nullable=False, default=datetime.utcnow)


ModelType = Union[
    Type[Study],
    Type[OmicsProcessing],
    Type[DataObject],
    Type[Biosample],
    Type[ReadsQC],
    Type[MetagenomeAssembly],
    Type[MetatranscriptomeAssembly],
    Type[MetagenomeAnnotation],
    Type[MetatranscriptomeAnnotation],
    Type[MetaproteomicAnalysis],
    Type[MAGsAnalysis],
    Type[ReadBasedAnalysis],
    Type[NOMAnalysis],
    Type[MetabolomicsAnalysis],
    Type[Metatranscriptome],
    Type[GeneFunction],
    Type[Base],
]

workflow_activity_types = [
    ReadsQC,
    MetagenomeAssembly,
    MetatranscriptomeAssembly,
    MetagenomeAnnotation,
    MetatranscriptomeAnnotation,
    MetaproteomicAnalysis,
    MAGsAnalysis,
    ReadBasedAnalysis,
    NOMAnalysis,
    MetabolomicsAnalysis,
    Metatranscriptome,
]


# denormalized tables
# These tables store aggregated gene function annotation data. The aggregations
# are generated in mongo and these tables are built during the ingeset of the
# associated pipelines
class MGAGeneFunctionAggregation(Base):
    __tablename__ = "mga_gene_function_aggregation"

    metagenome_annotation_id = Column(String, ForeignKey(MetagenomeAnnotation.id), primary_key=True)
    gene_function_id = Column(String, ForeignKey(GeneFunction.id), primary_key=True)
    count = Column(BigInteger, nullable=False)


class MetaPGeneFunctionAggregation(Base):
    __tablename__ = "metap_gene_function_aggregation"

    metaproteomic_analysis_id = Column(
        String, ForeignKey("metaproteomic_analysis.id"), primary_key=True
    )
    gene_function_id = Column(String, ForeignKey(GeneFunction.id), primary_key=True)
    count = Column(BigInteger, nullable=False)
    best_protein = Column(Boolean, nullable=False)


class MetaTGeneFunctionAggregation(Base):
    __tablename__ = "metat_gene_function_aggregation"

    metatranscriptome_annotation_id = Column(
        String, ForeignKey(MetatranscriptomeAnnotation.id), primary_key=True
    )
    gene_function_id = Column(String, ForeignKey(GeneFunction.id), primary_key=True)
    count = Column(BigInteger, nullable=False)


# Used to store a reference to a user requested zip download.  This is stored
# in a table primarily to avoid a large query string in the zip download GET
# endpoint. Since the GET endpoint cannot be protected by Bearer token auth,
# these rows are marked as expired after the first download. In the future,
# we could also expire these rows after a certain amount of time.
class BulkDownload(Base):
    __tablename__ = "bulk_download"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    created = Column(DateTime, nullable=False, default=datetime.utcnow)

    # information about the requestor (as in the FileDownload table)
    orcid = Column(String, nullable=False)
    ip = Column(String, nullable=False)
    user_agent = Column(String, nullable=True)

    # the list of conditions on the biosample query `List[ConditionSchema]`
    conditions = Column(JSONB, nullable=False)

    # the filter on data objects `List[DataObjectFilter]`
    filter = Column(JSONB, nullable=True)

    expired = Column(Boolean, nullable=False, default=False)


class BulkDownloadDataObject(Base):
    __tablename__ = "bulk_download_data_object"

    bulk_download_id = Column(UUID(as_uuid=True), ForeignKey(BulkDownload.id), primary_key=True)
    data_object_id = Column(String, ForeignKey(DataObject.id), primary_key=True)

    # the path inside the zip file
    path = Column(String, nullable=False)

    bulk_download = relationship(
        BulkDownload, backref=backref("files", lazy="joined", cascade="all")
    )
    data_object = relationship(
        DataObject, lazy="joined", cascade="all", backref="bulk_download_entities"
    )


Index("bulk_download_data_object_id_idx", BulkDownloadDataObject.data_object_id)


class EnvoTree(Base):
    __tablename__ = "envo_tree"

    id = Column(String, primary_key=True)
    parent_id = Column(String, index=True)


class User(Base):
    __tablename__ = "user_logins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    orcid = Column(String, nullable=False)
    name = Column(String)
    email = Column(String, nullable=True)
    is_admin = Column(Boolean, nullable=False, default=False)


class SubmissionEditorRole(str, enum.Enum):
    editor = "editor"
    owner = "owner"
    viewer = "viewer"
    metadata_contributor = "metadata_contributor"
    reviewer = "reviewer"


class SubmissionSourceClient(str, enum.Enum):
    submission_portal = "submission_portal"
    field_notes = "field_notes"
    nmdc_edge = "nmdc_edge"


class SubmissionMetadata(Base):
    __tablename__ = "submission_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    author_orcid = Column(String, nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(String, nullable=False, default="in-progress")
    metadata_submission = Column(JSONB, nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey(User.id))
    study_name = Column(String, nullable=True)
    templates = Column(JSONB, nullable=True)

    # The client which initially created the submission. A null value indicates it was created by
    # an "unregistered" client. This could be legitimate usage, but it should be monitored.
    source_client = Column(Enum(SubmissionSourceClient), nullable=True)

    author = relationship(
        "User", foreign_keys=[author_id], primaryjoin="SubmissionMetadata.author_id == User.id"
    )

    # Power the lock/unlock mechanism
    locked_by_id = Column(UUID(as_uuid=True), ForeignKey(User.id))
    locked_by = relationship(
        "User",
        foreign_keys=[locked_by_id],
        primaryjoin="SubmissionMetadata.locked_by_id == User.id",
    )
    lock_updated = Column(DateTime, nullable=True, default=datetime.utcnow)

    # Roles
    roles = relationship("SubmissionRole", back_populates="submission")

    @property
    def editors(self) -> list[str]:
        return [
            role.user_orcid
            for role in self.roles  # type: ignore
            if role.role == SubmissionEditorRole.editor
        ]

    @property
    def viewers(self) -> list[str]:
        return [
            role.user_orcid
            for role in self.roles  # type: ignore
            if role.role == SubmissionEditorRole.viewer
        ]

    @property
    def metadata_contributors(self) -> list[str]:
        return [
            role.user_orcid
            for role in self.roles  # type: ignore
            if role.role == SubmissionEditorRole.metadata_contributor
        ]

    @property
    def owners(self) -> list[str]:
        return [
            role.user_orcid
            for role in self.roles  # type: ignore
            if role.role == SubmissionEditorRole.owner
        ]


class SubmissionRole(Base):
    __tablename__ = "submission_role"
    __table_args__ = (UniqueConstraint("submission_id", "user_orcid"),)

    submission_id = Column(UUID(as_uuid=True), ForeignKey(SubmissionMetadata.id), primary_key=True)
    # Use a plain string column over FK to support adding permissions for people who
    # haven't yet signed into the Data Portal
    user_orcid = Column(String, primary_key=True)
    role = Column(Enum(SubmissionEditorRole))

    submission = relationship("SubmissionMetadata", back_populates="roles")


class AuthorizationCode(Base):
    __tablename__ = "authorization_code"

    code = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey(User.id), nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.utcnow)
    redirect_uri = Column(String, nullable=False)
    exchanged = Column(Boolean, nullable=False, default=False)

    user = relationship(
        "User", foreign_keys=[user_id], primaryjoin="AuthorizationCode.user_id == User.id"
    )


class InvalidatedToken(Base):
    __tablename__ = "invalidated_token"

    token = Column(String, primary_key=True)
