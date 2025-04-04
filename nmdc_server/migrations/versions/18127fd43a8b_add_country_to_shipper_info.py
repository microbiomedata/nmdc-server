"""add-country-to-shipper-info

Revision ID: 18127fd43a8b
Revises: 4b2d6ee63752
Create Date: 2025-01-24 15:53:45.897421

"""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from alembic import op
from pydantic import BaseModel
from sqlalchemy import Column, orm
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# revision identifiers, used by Alembic.
revision: str = "18127fd43a8b"
down_revision: Optional[str] = "4b2d6ee63752"
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
    country: str = ""


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
    datasetDoi: str = ""
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
        if isinstance(metadata_submission, List):
            continue

        if not metadata_submission.get("contextForm", None):
            context_form = ContextForm().dict()
            context_form["datasetDoi"] = metadata_submission.get("multiOmicsForm", {}).get(
                "datasetDoi", ""
            )
            metadata_submission["contextForm"] = context_form
        if not metadata_submission.get("addressForm"):
            metadata_submission["addressForm"] = AddressForm().dict()

        if metadata_submission.get("addressForm"):
            address_form = metadata_submission["addressForm"]
            if not address_form.get("shipper", {}).get("country"):
                address_form["shipper"]["country"] = "USA"
        mappings.append({"id": submission_metadata.id, "metadata_submission": metadata_submission})
    session.bulk_update_mappings(SubmissionMetadata, mappings)
    session.commit()


def downgrade():
    session = orm.Session(bind=op.get_bind())
    mappings = []
    for submission_metadata in session.query(SubmissionMetadata):
        metadata_submission = submission_metadata.metadata_submission
        if isinstance(metadata_submission, List):
            continue
        if metadata_submission.get("addressForm"):
            address_form = metadata_submission["addressForm"]
            if address_form.get("shipper", {}).get("country") == "USA":
                del address_form["shipper"]["country"]
        mappings.append({"id": submission_metadata.id, "metadata_submission": metadata_submission})
    session.bulk_update_mappings(SubmissionMetadata, mappings)
    session.commit()
