"""submission schema v1.0.0

In v1.0.0 of the submission schema some slot names on the
SampleData class were changed. This migration makes the
corresponding renames on the JSON data stored in the
submission_metadata table.

Additionally there was some inconsistency in what was stored
in the templates array. This migration also ensures that the
strings always correspond to keys of the HARMONIZER_TEMPLATES
object in harmonizerApi.ts.

Revision ID: 7b9f5a789198
Revises: b96ecfffa792
Create Date: 2023-03-21 23:29:41.957897

"""
from typing import Optional
from uuid import uuid4

from alembic import op
from sqlalchemy import Column, orm
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base

# revision identifiers, used by Alembic.
revision: str = "7b9f5a789198"
down_revision: Optional[str] = "b96ecfffa792"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


Base = declarative_base()


class SubmissionMetadata(Base):
    __tablename__ = "submission_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    metadata_submission = Column(JSONB, nullable=False)


def replace_key(sample_data, from_key, to_key):
    if from_key in sample_data:
        sample_data[to_key] = sample_data[from_key]
        del sample_data[from_key]


def replace_list_item(list_data, index, from_value, to_value):
    if not list_data:
        return
    if list_data[index] == from_value:
        list_data[index] = to_value


RENAMED_SLOTS = [
    # ( old name, new name )
    ("hcr-cores_data", "hcr_cores_data"),
    ("hcr-fluids-swabs_data", "hcr_fluids_swabs_data"),
    ("host-associated_data", "host_associated_data"),
    ("misc-envs_data", "misc_envs_data"),
    ("plant-associated_data", "plant_associated_data"),
]

RENAMED_ENV_TEMPLATE_KEYS = [
    ("built_env", "built environment"),
    ("hcr-cores", "hydrocarbon resources-cores"),
    ("hcr-fluids-swabs", "hydrocarbon resources-fluids_swabs"),
    ("biofilm", "microbial mat_biofilm"),
    ("misc-envs", "miscellaneous natural or artificial environment"),
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

        for rename in RENAMED_SLOTS:
            replace_key(sample_data, rename[0], rename[1])

        for rename in RENAMED_ENV_TEMPLATE_KEYS:
            replace_list_item(metadata_submission.get("templates"), 0, rename[0], rename[1])

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

        for rename in RENAMED_SLOTS:
            replace_key(sample_data, rename[1], rename[0])

        for rename in RENAMED_ENV_TEMPLATE_KEYS:
            replace_list_item(metadata_submission.get("templates"), 0, rename[1], rename[0])

        mappings.append({"id": submission_metadata.id, "metadata_submission": metadata_submission})

    session.bulk_update_mappings(SubmissionMetadata, mappings)
    session.commit()
