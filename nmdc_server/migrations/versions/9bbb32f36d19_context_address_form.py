"""additional submission build wizard step

Revision ID: 9bbb32f36d19
Revises: ae7a3eba08c5
Create Date: 2023-02-02 19:54:44.340586

"""
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from pydantic import BaseModel
from sqlalchemy import Column, orm
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# revision identifiers, used by Alembic.
revision: str = "9bbb32f36d19"
down_revision: Optional[str] = "ae7a3eba08c5"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


# Redefine SubmissionMetadata, including only what we need for this migration
# to ensure this migration is self-contained.
# https://stackoverflow.com/questions/17547119/accessing-models-in-alembic-migrations
class SubmissionMetadata(Base):
    __tablename__ = "submission_metadata"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    metadata_submission = Column(JSONB, nullable=False)


# Similarly, redefine pydantic models for context_ and address_form
class NmcdAddress(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    line1: str = ""
    line2: str = ""
    city: str = ""
    state: str = ""
    postalCode: str = ""


class AddressForm(BaseModel):
    shipper: NmcdAddress = NmcdAddress()
    expectedShippingDate: Optional[datetime] = None
    shippingConditions: str = ""
    sample: str = ""
    description: str = ""
    experimentalGoals: str = ""
    randomization: str = ""
    usdaRegulated: Optional[bool] = None
    permitNumber: str = ""
    biosafetyLevel: str = ""
    irpOrHipaa: Optional[bool] = None
    irbNumber: str = ""
    irbAddress: NmcdAddress = NmcdAddress()
    comments: str = ""


class ContextForm(BaseModel):
    dataGenerated: Optional[bool] = None
    facilityGenerated: Optional[bool] = None
    facilities: List[str] = []
    award: Optional[str] = None
    otherAward: str = ""


def upgrade():
    session = orm.Session(bind=op.get_bind())
    mappings = []
    for submission_metadata in session.query(SubmissionMetadata):
        metadata_submission = submission_metadata.metadata_submission
        if not metadata_submission.get("context_form"):
            metadata_submission["context_form"] = ContextForm().dict()
        if not metadata_submission.get("address_form"):
            metadata_submission["address_form"] = AddressForm().dict()
        mappings.append({"id": submission_metadata.id, "metadata_submission": metadata_submission})
    session.bulk_update_mappings(SubmissionMetadata, mappings)
    session.commit()


def downgrade():
    session = orm.Session(bind=op.get_bind())
    mappings = []
    for submission_metadata in session.query(SubmissionMetadata):
        metadata_submission = submission_metadata.metadata_submission
        if metadata_submission["context_form"]:
            del metadata_submission["context_form"]
        if metadata_submission["address_form"]:
            del metadata_submission["address_form"]
        mappings.append({"id": submission_metadata.id, "metadata_submission": metadata_submission})
    session.bulk_update_mappings(SubmissionMetadata, mappings)
    session.commit()
