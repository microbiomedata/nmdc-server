"""Update JGI submission-schema slot names

Revision ID: 0cb677fa8d5e
Revises: e27443f0837e
Create Date: 2025-08-06 19:53:09.430148

"""

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


RENAMED_SLOTS = [
    # ( old name, new name )
    ("dna_absorb1", "nuc_acid_absorb1"),
    ("rna_absorb1", "nuc_acid_absorb1"),
    ("dna_absorb2", "nuc_acid_absorb2"),
    ("rna_absorb2", "nuc_acid_absorb2"),
    ("dna_concentration", "nuc_acid_concentration"),
    ("rna_concentration", "nuc_acid_concentration"),
    ("dna_cont_type", "cont_type"),
    ("rna_cont_type", "cont_type"),
    ("dna_cont_well", "cont_well"),
    ("rna_cont_well", "cont_well"),
    ("dna_container_id", "container_name"),
    ("rna_container_id", "container_name"),
    ("dna_dnase", "dnase"),
    ("dnase_rna", "dnase"),
    ("dna_samp_id", "jgi_samp_id"),
    ("rna_samp_id", "jgi_samp_id"),
    ("dna_sample_format", "jgi_sample_format"),
    ("rna_sample_format", "jgi_sample_format"),
    ("dna_sample_name", "jgi_sample_name"),
    ("rna_sample_name", "jgi_sample_name"),
    ("dna_seq_project", "jgi_seq_project"),
    ("rna_seq_project", "jgi_seq_project"),
    ("dna_seq_project_name", "jgi_seq_project_name"),
    ("rna_seq_project_name", "jgi_seq_project_name"),
    ("dna_volume", "jgi_sample_volume"),
    ("rna_volume", "jgi_sample_volume"),
]


def do_rename(mapping: dict[str, str]):
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

        for tab, rows in sample_data.items():
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                for old_key, new_key in mapping.items():
                    if old_key in row:
                        row[new_key] = row.pop(old_key)

        mappings.append({"id": submission_metadata.id, "metadata_submission": metadata_submission})

    session.bulk_update_mappings(SubmissionMetadata, mappings)
    session.commit()


def upgrade():
    do_rename({old: new for old, new in RENAMED_SLOTS})


def downgrade():
    do_rename({new: old for old, new in RENAMED_SLOTS})
