"""Update award DOI from string to class containing provider and value

Revision ID: 6cb0b331ce8c
Revises: 997064dd504d
Create Date: 2025-06-24 19:42:22.295714

"""

from typing import Optional
from uuid import uuid4

from alembic import op
from sqlalchemy import Column, orm
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
# revision identifiers, used by Alembic.
revision: str = "6cb0b331ce8c"
down_revision: Optional[str] = "997064dd504d"
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

        if isinstance(metadata_submission, list):
            continue

        multi_omics_form = metadata_submission["multiOmicsForm"]

        if multi_omics_form.get("awardDois", None):
            values = multi_omics_form["awardDois"]
            values = values.split(",")
            new_dois = []
            for val in values:
                new_dois.append({"value": val, "provider": ""})

            multi_omics_form["awardDois"] = new_dois
        mappings.append({"id": submission_metadata.id, "metadata_submission": metadata_submission})

    session.bulk_update_mappings(SubmissionMetadata, mappings)
    session.commit()
    # ### end Alembic commands ###


def downgrade():
    session = orm.Session(bind=op.get_bind())
    mappings = []
    for submission_metadata in session.query(SubmissionMetadata):
        metadata_submission = submission_metadata.metadata_submission

        if isinstance(metadata_submission, list):
            continue

        multi_omics_form = metadata_submission["multiOmicsForm"]

        if multi_omics_form.get("awardDois", None):
            values = multi_omics_form["awardDois"]
            new_dois = []
            for dict in values:
                new_dois.append(dict["value"])

            multi_omics_form["awardDois"] = new_dois
        mappings.append({"id": submission_metadata.id, "metadata_submission": metadata_submission})

    session.bulk_update_mappings(SubmissionMetadata, mappings)
    session.commit()
    # ### end Alembic commands ###
