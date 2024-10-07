"""Update datasetDoi on context page

Part of the ongoing additions to the submission portal includes updating
the context form's datasetDoi to awardDoi. Doing this also changes the field to be an array/list.
This migration will update the name of datasetDoi in existing entries to awardDoi, convert the field
to a list/array, and update any values that need it to be list
(such as comma delimited lists users have entered).

Revision ID: 988105f6581d
Revises: 5fb9910ca8e6
Create Date: 2024-10-07 18:14:38.465850

"""

from typing import Optional
from uuid import uuid4

from alembic import op
from sqlalchemy import Column, orm
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
# revision identifiers, used by Alembic.
revision: str = "988105f6581d"
down_revision: Optional[str] = "5fb9910ca8e6"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


class SubmissionMetadata(Base):
    __tablename__ = "submission_metadata"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    metadata_submission = Column(JSONB, nullable=False)


def upgrade():
    session = orm.Session(bind=op.get_bind())
    mappings = []
    for submission_metadata in session.query(SubmissionMetadata):
        metadata_submission = submission_metadata.metadata_submission
        context_form = metadata_submission["contextForm"]

        if not context_form.get("awardDoi", None) and context_form.get("datasetDoi", None):
            holder = context_form["datasetDoi"]
            holder = holder.split(",")
            context_form["awardDoi"] = holder
            context_form.pop("datasetDoi", None)
        mappings.append({"id": submission_metadata.id, "metadata_submission": metadata_submission})

    session.bulk_update_mappings(SubmissionMetadata, mappings)
    session.commit()


def downgrade():
    session = orm.Session(bind=op.get_bind())
    mappings = []
    for submission_metadata in session.query(SubmissionMetadata):
        metadata_submission = submission_metadata.metadata_submission
        context_form = metadata_submission["contextForm"]

        if not context_form.get("datasetDoi", None) and context_form.get("awardDoi", None):
            holder = context_form["awardDoi"]
            context_form["datasetDoi"] = ",".join(map(str, holder))
            context_form.pop("awardDoi", None)
        mappings.append({"id": submission_metadata.id, "metadata_submission": metadata_submission})

    session.bulk_update_mappings(SubmissionMetadata, mappings)
    session.commit()
