from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional, Type, Union
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Table,
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


def gold_url(base: str, id: str) -> Optional[str]:
    if id.startswith("gold:"):
        return f"{base}{id[5:]}"
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

    # a PI profile image... originally we didn't have a place to store static content
    # so the image data is placed in the database.
    image = Column(LargeBinary, nullable=True)


# Caches information from doi.org
class DOIInfo(Base):
    __tablename__ = "doi_info"

    id = Column(String, primary_key=True)
    info = Column(JSONB, nullable=False, default=dict)


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
    doi = Column(String, ForeignKey("doi_info.id"), nullable=True)
    multiomics = Column(Integer, nullable=False, default=0)

    # These query expressions are a way to inject additional aggregation information
    # into the query at search time.  See `with_expression` usage in `query.py`.
    # TODO: Specify a default expression so that sample counts are present in
    #       non-search responses.
    sample_count = query_expression()
    omics_counts = query_expression()
    omics_processing_counts = query_expression()

    principal_investigator_id = Column(
        UUID(as_uuid=True), ForeignKey("principal_investigator.id"), nullable=False
    )
    principal_investigator = relationship("PrincipalInvestigator", cascade="all")
    principal_investigator_name = association_proxy("principal_investigator", "name")

    @property
    def principal_investigator_image_url(self):
        return f"/api/principal_investigator/{self.principal_investigator_id}"

    principal_investigator_websites = relationship("StudyWebsite", cascade="all", lazy="joined")
    publication_dois = relationship("StudyPublication", cascade="all", lazy="joined")
    doi_object = relationship("DOIInfo", cascade="all", lazy="joined")

    doi_info = association_proxy("doi_object", "info")

    @property
    def open_in_gold(self) -> Optional[str]:
        return gold_url("https://gold.jgi.doe.gov/study?id=", self.id)

    @property
    def publication_doi_info(self) -> Dict[str, Any]:
        doi_info = {
            d.publication.doi: d.publication.doi_object.info
            for d in self.publication_dois  # type: ignore
        }
        if self.doi:
            doi_info[self.doi] = self.doi_info
        return doi_info


class Biosample(Base, AnnotatedModel):
    __tablename__ = "biosample"

    add_date = Column(DateTime, nullable=True)
    mod_date = Column(DateTime, nullable=True)
    collection_date = Column(DateTime, nullable=True)
    depth = Column(Float, nullable=True)
    env_broad_scale_id = Column(String, ForeignKey(EnvoTerm.id), nullable=True)
    env_local_scale_id = Column(String, ForeignKey(EnvoTerm.id), nullable=True)
    env_medium_id = Column(String, ForeignKey(EnvoTerm.id), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    study_id = Column(String, ForeignKey("study.id"), nullable=False)
    multiomics = Column(Integer, nullable=False, default=0)

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
    biosample_id = Column(String, ForeignKey("biosample.id"), nullable=True)
    biosample = relationship("Biosample", backref="omics_processing")
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
    file_size_bytes = Column(BigInteger, nullable=False)
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

    input_read_count = Column(BigInteger, nullable=False)
    input_read_bases = Column(BigInteger, nullable=False)
    output_read_count = Column(BigInteger, nullable=False)
    output_read_bases = Column(BigInteger, nullable=False)

    inputs = input_relationship(reads_qc_input_association)
    outputs = output_relationship(reads_qc_output_association)


metagenome_assembly_input_association = input_association("metagenome_assembly")
metagenome_assembly_output_association = output_association("metagenome_assembly")


class MetagenomeAssembly(Base, PipelineStep):
    __tablename__ = "metagenome_assembly"

    scaffolds = Column(BigInteger, nullable=False)
    contigs = Column(BigInteger, nullable=False)
    scaf_bp = Column(BigInteger, nullable=False)
    contig_bp = Column(BigInteger, nullable=False)
    scaf_N50 = Column(BigInteger, nullable=False)
    scaf_L50 = Column(BigInteger, nullable=False)
    ctg_N50 = Column(BigInteger, nullable=False)
    ctg_L50 = Column(BigInteger, nullable=False)
    scaf_N90 = Column(BigInteger, nullable=False)
    scaf_L90 = Column(BigInteger, nullable=False)
    ctg_N90 = Column(BigInteger, nullable=False)
    ctg_L90 = Column(BigInteger, nullable=False)
    scaf_max = Column(BigInteger, nullable=False)
    ctg_max = Column(BigInteger, nullable=False)
    scaf_n_gt50K = Column(BigInteger, nullable=False)
    scaf_l_gt50k = Column(BigInteger, nullable=False)
    scaf_pct_gt50K = Column(BigInteger, nullable=False)
    num_input_reads = Column(BigInteger, nullable=False)
    num_aligned_reads = Column(BigInteger, nullable=False)

    scaf_logsum = Column(Float, nullable=False)
    scaf_powsum = Column(Float, nullable=False)
    ctg_logsum = Column(Float, nullable=False)
    ctg_powsum = Column(Float, nullable=False)
    asm_score = Column(Float, nullable=False)
    gap_pct = Column(Float, nullable=False)
    gc_avg = Column(Float, nullable=False)
    gc_std = Column(Float, nullable=False)

    inputs = input_relationship(metagenome_assembly_input_association)
    outputs = output_relationship(metagenome_assembly_output_association)


metagenome_annotation_input_association = input_association("metagenome_annotation")
metagenome_annotation_output_association = output_association("metagenome_annotation")


class MetagenomeAnnotation(Base, PipelineStep):
    __tablename__ = "metagenome_annotation"

    gene_functions = relationship("MGAGeneFunction")

    inputs = input_relationship(metagenome_annotation_input_association)
    outputs = output_relationship(metagenome_annotation_output_association)


metaproteomic_analysis_input_association = input_association("metaproteomic_analysis")
metaproteomic_analysis_output_association = output_association("metaproteomic_analysis")


class MetaproteomicAnalysis(Base, PipelineStep):
    __tablename__ = "metaproteomic_analysis"

    inputs = input_relationship(metaproteomic_analysis_input_association)
    outputs = output_relationship(metaproteomic_analysis_output_association)


mags_analysis_input_association = input_association("mags_analysis")
mags_analysis_output_association = output_association("mags_analysis")


class MetaproteomicPeptide(Base):
    __tablename__ = "metaproteomic_peptide"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    metaproteomic_analysis_id = Column(
        String, ForeignKey("metaproteomic_analysis.id"), nullable=False
    )

    peptide_sequence = Column(String, nullable=False)
    peptide_sum_masic_abundance = Column(BigInteger, nullable=False)
    peptide_spectral_count = Column(BigInteger, nullable=False)
    best_protein = Column(String, ForeignKey("mga_gene_function.subject"), nullable=False)
    min_q_value = Column(Float, nullable=False)

    best_protein_object = relationship("MGAGeneFunction")
    metaproteomic_analysis = relationship(
        MetaproteomicAnalysis, backref="has_peptide_quantifications"
    )


class PeptideMGAGeneFunction(Base):
    __tablename__ = "peptide_mga_gene_function"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    subject = Column(String, ForeignKey("mga_gene_function.subject"), nullable=False)
    metaproteomic_peptide_id = Column(
        UUID(as_uuid=True), ForeignKey("metaproteomic_peptide.id"), nullable=False
    )

    mga_gene_function = relationship("MGAGeneFunction")
    metaproteomic_peptide = relationship("MetaproteomicPeptide")

    @property
    def gene_function(self) -> str:
        return self.mga_gene_function.gene_function_id


class MAGsAnalysis(Base, PipelineStep):
    __tablename__ = "mags_analysis"

    input_contig_num = Column(BigInteger, nullable=False)
    too_short_contig_num = Column(BigInteger, nullable=False)
    lowDepth_contig_num = Column(BigInteger, nullable=False)
    unbinned_contig_num = Column(BigInteger, nullable=False)
    binned_contig_num = Column(BigInteger, nullable=False)

    inputs = input_relationship(mags_analysis_input_association)
    outputs = output_relationship(mags_analysis_output_association)


class MAG(Base):
    __tablename__ = "mag"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    mags_analysis_id = Column(String, ForeignKey("mags_analysis.id"), nullable=False)
    bin_name = Column(String, nullable=False)
    number_of_contig = Column(BigInteger, nullable=False)
    completeness = Column(Float, nullable=False)
    contamination = Column(Float, nullable=False)
    gene_count = Column(BigInteger, nullable=False)
    bin_quality = Column(String, nullable=False)
    num_16s = Column(BigInteger, nullable=False)
    num_5s = Column(BigInteger, nullable=False)
    num_23s = Column(BigInteger, nullable=False)
    num_tRNA = Column(BigInteger, nullable=False)

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
    __tablename__ = "metatranscriptome"

    inputs = input_relationship(metatranscriptome_input_association)
    outputs = output_relationship(metatranscriptome_output_association)


metabolomics_analysis_input_association = input_association("metabolomics_analysis")
metabolomics_analysis_output_association = output_association("metabolomics_analysis")


class MetabolomicsAnalysis(Base, PipelineStep):
    __tablename__ = "metabolomics_analysis"

    used = Column(String, nullable=False)
    has_calibration = Column(String, nullable=False)

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


class Publication(Base):
    __tablename__ = "publication"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    doi = Column(String, ForeignKey("doi_info.id"), nullable=False, unique=True)

    doi_object = relationship("DOIInfo", cascade="all", lazy="joined")


class StudyPublication(Base):
    __tablename__ = "study_publication"

    study_id = Column(String, ForeignKey("study.id"), primary_key=True)
    publication_id = Column(UUID(as_uuid=True), ForeignKey("publication.id"), primary_key=True)

    publication = relationship(Publication, cascade="all")


# This table contains KO terms detected in metagenome and metaproteomic workflow
# activities.  In terms of size, this table and particularly the MGAGeneFunction
# table linking with workflow activities are orders of magnitude larger than
# the other tables.
class GeneFunction(Base):
    __tablename__ = "gene_function"

    id = Column(String, primary_key=True)


class MGAGeneFunction(Base):  # metagenome annotation
    __tablename__ = "mga_gene_function"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    metagenome_annotation_id = Column(
        String, ForeignKey("metagenome_annotation.id"), nullable=False
    )
    gene_function_id = Column(String, ForeignKey("gene_function.id"), nullable=False)
    subject = Column(String, nullable=False, unique=True)

    function = relationship(GeneFunction)


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
    Type[MetagenomeAnnotation],
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
    MetagenomeAnnotation,
    MetaproteomicAnalysis,
    MAGsAnalysis,
    ReadBasedAnalysis,
    NOMAnalysis,
    MetabolomicsAnalysis,
    Metatranscriptome,
]


# denormalized tables
# To improve performance of gene function queries a denormalized representation of gene functions
# detected in MetaG and MetaP workflow activies is generated after ingestion.  This is done using
# the custom SQL embedded in the populate methods.
class MGAGeneFunctionAggregation(Base):
    __tablename__ = "mga_gene_function_aggregation"

    metagenome_annotation_id = Column(String, ForeignKey(MetagenomeAnnotation.id), primary_key=True)
    gene_function_id = Column(String, ForeignKey(GeneFunction.id), primary_key=True)
    count = Column(BigInteger, nullable=False)

    @classmethod
    def populate(cls, db: Session):
        """Populate denormalized gene function table."""
        db.execute(
            f"""
            INSERT INTO
                {cls.__tablename__} (metagenome_annotation_id, gene_function_id, count)
            SELECT metagenome_annotation_id, gene_function_id, count(*) as count
            FROM mga_gene_function GROUP BY metagenome_annotation_id, gene_function_id
            ON CONFLICT (metagenome_annotation_id, gene_function_id)
            DO UPDATE SET count = excluded.count;
        """
        )


class MetaPGeneFunctionAggregation(Base):
    __tablename__ = "metap_gene_function_aggregation"

    metaproteomic_analysis_id = Column(
        String, ForeignKey("metaproteomic_analysis.id"), primary_key=True
    )
    gene_function_id = Column(String, ForeignKey(GeneFunction.id), primary_key=True)
    count = Column(BigInteger, nullable=False)
    best_protein = Column(Boolean, nullable=False)

    @classmethod
    def populate(cls, db: Session):
        """Populate denormalized gene function table."""
        db.execute(
            f"""
            INSERT INTO
                {cls.__tablename__}
                (metaproteomic_analysis_id, gene_function_id, count, best_protein)
            SELECT
                metaproteomic_analysis.id,
                mga_gene_function.gene_function_id,
                count(*) AS count,
                bool_or(metaproteomic_peptide.best_protein = mga_gene_function.subject)
                    AS best_protein
            FROM metaproteomic_analysis
            JOIN metaproteomic_peptide
                ON metaproteomic_peptide.metaproteomic_analysis_id = metaproteomic_analysis.id
            JOIN peptide_mga_gene_function
                ON peptide_mga_gene_function.metaproteomic_peptide_id = metaproteomic_peptide.id
            JOIN mga_gene_function
                ON mga_gene_function.subject = peptide_mga_gene_function.subject
            GROUP BY metaproteomic_analysis.id, mga_gene_function.gene_function_id
            ON CONFLICT (metaproteomic_analysis_id, gene_function_id)
            DO UPDATE
            SET count = excluded.count, best_protein = excluded.best_protein;
        """
        )


# Used to store a reference to a user requested zip download.  This is stored
# in a table primarily to avoid a large query string in the zip download GET
# endpoint.
# TODO: consider expiring rows from this table
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


class EnvoTree(Base):
    __tablename__ = "envo_tree"

    id = Column(String, primary_key=True)
    parent_id = Column(String, index=True)
