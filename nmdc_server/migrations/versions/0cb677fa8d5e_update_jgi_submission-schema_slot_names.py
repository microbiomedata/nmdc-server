"""Update JGI submission-schema slot names

Revision ID: 0cb677fa8d5e
Revises: e27443f0837e
Create Date: 2025-08-06 19:53:09.430148

"""

from collections import namedtuple
from typing import Optional
from uuid import uuid4

from alembic import op
from sqlalchemy import Column, orm
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base

# revision identifiers, used by Alembic.
revision: str = "0cb677fa8d5e"
down_revision: Optional[str] = "e27443f0837e"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


Base = declarative_base()


class SubmissionMetadata(Base):
    __tablename__ = "submission_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    metadata_submission = Column(JSONB, nullable=False)


RenamedSlot = namedtuple("RenamedSlot", ["old_name_mg", "old_name_mt", "new_name"])


RENAMED_SLOTS: list[RenamedSlot] = [
    RenamedSlot("dna_absorb1", "rna_absorb1", "nuc_acid_absorb1"),
    RenamedSlot("dna_absorb2", "rna_absorb2", "nuc_acid_absorb2"),
    RenamedSlot("dna_concentration", "rna_concentration", "nuc_acid_concentration"),
    RenamedSlot("dna_cont_type", "rna_cont_type", "cont_type"),
    RenamedSlot("dna_cont_well", "rna_cont_well", "cont_well"),
    RenamedSlot("dna_container_id", "rna_container_id", "container_name"),
    RenamedSlot("dna_dnase", "dnase_rna", "dnase"),
    RenamedSlot("dna_samp_id", "rna_samp_id", "jgi_samp_id"),
    RenamedSlot("dna_sample_format", "rna_sample_format", "jgi_sample_format"),
    RenamedSlot("dna_sample_name", "rna_sample_name", "jgi_sample_name"),
    RenamedSlot("dna_seq_project", "rna_seq_project", "jgi_seq_project"),
    RenamedSlot("dna_seq_project_name", "rna_seq_project_name", "jgi_seq_project_name"),
    RenamedSlot("dna_volume", "rna_volume", "jgi_sample_volume"),
]


def upgrade():
    session = orm.Session(bind=op.get_bind())
    mappings = []
    for submission_metadata in session.query(SubmissionMetadata):
        metadata_submission = submission_metadata.metadata_submission

        if isinstance(metadata_submission, list):
            continue

        sample_data = metadata_submission.get("sampleData")

        if sample_data is None or not isinstance(sample_data, dict):
            print(f"WARNING: sampleData not in migratable format for {submission_metadata.id}")
            continue

        for tab_key, rows in sample_data.items():
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                for rename in RENAMED_SLOTS:
                    if "jgi_mg" in tab_key and rename.old_name_mg in row:
                        row[rename.new_name] = row.pop(rename.old_name_mg)
                    elif "jgi_mt" in tab_key and rename.old_name_mt in row:
                        row[rename.new_name] = row.pop(rename.old_name_mt)

        mappings.append({"id": submission_metadata.id, "metadata_submission": metadata_submission})

    session.bulk_update_mappings(SubmissionMetadata, mappings)
    session.commit()


def downgrade():
    session = orm.Session(bind=op.get_bind())
    mappings = []
    for submission_metadata in session.query(SubmissionMetadata):
        metadata_submission = submission_metadata.metadata_submission

        if isinstance(metadata_submission, list):
            continue

        sample_data = metadata_submission.get("sampleData")

        if sample_data is None or not isinstance(sample_data, dict):
            print(f"WARNING: sampleData not in migratable format for {submission_metadata.id}")
            continue

        for tab_key, rows in sample_data.items():
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                for rename in RENAMED_SLOTS:
                    if rename.new_name in row:
                        if "jgi_mg" in tab_key:
                            row[rename.old_name_mg] = row.pop(rename.new_name)
                        elif "jgi_mt" in tab_key:
                            row[rename.old_name_mt] = row.pop(rename.new_name)

        mappings.append({"id": submission_metadata.id, "metadata_submission": metadata_submission})

    session.bulk_update_mappings(SubmissionMetadata, mappings)
    session.commit()
