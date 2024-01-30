"""remove irb information

Revision ID: b96ecfffa792
Revises: 9bbb32f36d19
Create Date: 2023-03-01 19:54:23.116184

"""

from typing import Optional
from uuid import uuid4

from alembic import op
from pydantic import BaseModel
from sqlalchemy import Column, orm
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base

# revision identifiers, used by Alembic.
revision: str = "b96ecfffa792"
down_revision: Optional[str] = "9bbb32f36d19"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


Base = declarative_base()


class SubmissionMetadata(Base):
    __tablename__ = "submission_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    metadata_submission = Column(JSONB, nullable=False)


class NmcdAddress(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    line1: str = ""
    line2: str = ""
    city: str = ""
    state: str = ""
    postalCode: str = ""


def upgrade():
    session = orm.Session(bind=op.get_bind())
    mappings = []
    for submission_metadata in session.query(SubmissionMetadata):
        metadata_submission = submission_metadata.metadata_submission

        if isinstance(metadata_submission, list):
            continue

        address_form = metadata_submission.get("address_form", None)

        if not address_form:
            continue

        if "irbNumber" in list(address_form):
            del address_form["irbNumber"]
        if "irbAddress" in list(address_form):
            del address_form["irbAddress"]
        if "irpOrHipaa" in list(address_form):
            address_form["irbOrHipaa"] = address_form["irpOrHipaa"]
            del address_form["irpOrHipaa"]
        else:
            address_form["irbOrHippa"] = None
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

        address_form = metadata_submission.get("address_form", None)
        if not address_form:
            continue

        address_form["irbNumber"] = ""
        address_form["irbAddress"] = NmcdAddress().dict()
        if "irbOrHipaa" in list(address_form):
            address_form["irpOrHipaa"] = address_form["irbOrHipaa"]
            del address_form["irbOrHipaa"]
        mappings.append({"id": submission_metadata.id, "metadata_submission": metadata_submission})
    session.bulk_update_mappings(SubmissionMetadata, mappings)
    session.commit()
