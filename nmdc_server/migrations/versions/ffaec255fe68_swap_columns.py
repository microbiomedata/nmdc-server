"""swap_columns

Revision ID: ffaec255fe68
Revises: eb9d9e3f3fbc
Create Date: 2022-08-25 02:13:12.732971

"""
from typing import Optional
from uuid import uuid4

from alembic import op
from sqlalchemy import Column, orm
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base

# revision identifiers, used by Alembic.
revision: str = "ffaec255fe68"
down_revision: Optional[str] = "eb9d9e3f3fbc"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None

Base = declarative_base()


class SubmissionMetadata(Base):
    __tablename__ = "submission_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    metadata_submission = Column(JSONB, nullable=False)


def upgrade():
    session = orm.Session(bind=op.get_bind())
    mappings = []
    for submission_metadata in session.query(SubmissionMetadata):
        metadata_submission = submission_metadata.metadata_submission
        new_rows = []
        for row in metadata_submission["sampleData"]:
            uid = row[0]
            name = row[1]
            row[0] = name
            row[1] = uid
            new_rows.append(row)
        metadata_submission["sampleData"] = new_rows
        mappings.append({"id": submission_metadata.id, "metadata_submission": metadata_submission})
    session.bulk_update_mappings(SubmissionMetadata, mappings)
    session.commit()


def downgrade():
    session = orm.Session(bind=op.get_bind())
    mappings = []
    for submission_metadata in session.query(SubmissionMetadata):
        metadata_submission = submission_metadata.metadata_submission
        new_rows = []
        for row in metadata_submission["sampleData"]:
            name = row[0]
            uid = row[1]
            row[0] = uid
            row[1] = name
            new_rows.append(row)
        metadata_submission["sampleData"] = new_rows
        mappings.append({"id": submission_metadata.id, "metadata_submission": metadata_submission})
    session.bulk_update_mappings(SubmissionMetadata, mappings)
    session.commit()
