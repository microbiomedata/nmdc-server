"""merge_context_multiomics

Revision ID: cf73ba2f0f85
Revises: efd01ffd23b2
Create Date: 2025-03-20 20:23:15.379005

"""

from typing import List, Optional
from uuid import uuid4

from alembic import op
from pydantic import BaseModel
from sqlalchemy import Column, orm
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# revision identifiers, used by Alembic.
revision: str = "cf73ba2f0f85"
down_revision: Optional[str] = "efd01ffd23b2"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


class SubmissionMetadata(Base):
    __tablename__ = "submission_metadata"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    metadata_submission = Column(JSONB, nullable=False)


class ContextForm(BaseModel):
    datasetDoi: str = ""
    dataGenerated: Optional[bool] = None
    facilityGenerated: Optional[bool] = None
    facilities: List[str] = []
    award: Optional[str] = None
    otherAward: str = ""


class StudyForm(BaseModel):
    alternativeNames: List[str]
    GOLDStudyId: str
    NCBIBioProjectId: str


class MultiOmicsForm(BaseModel):
    award: Optional[str] = None
    datasetDoi: str = ""
    dataGenerated: Optional[bool] = None
    facilities: List[str]
    facilityGenerated: Optional[bool] = None
    otherAward: str
    alternativeNames: List[str]
    GOLDStudyId: str
    NCBIBioProjectId: str


def upgrade():
    session = orm.Session(bind=op.get_bind())
    mappings = []
    for submission_metadata in session.query(SubmissionMetadata):
        metadata_submission = submission_metadata.metadata_submission
        if isinstance(metadata_submission, List):
            continue

        if metadata_submission.get("contextForm", None):
            context_form = metadata_submission.get("contextForm", {})
            multiomics_form = metadata_submission.get("multiomicsForm", {})

            multiomics_form.setdefault("datasetDoi", context_form.get("datasetDoi", ""))
            multiomics_form.setdefault("dataGenerated", context_form.get("dataGenerated", None))
            multiomics_form.setdefault(
                "facilityGenerated", context_form.get("facilityGenerated", None)
            )
            multiomics_form.setdefault("facilities", context_form.get("facilities", []))
            multiomics_form.setdefault("award", context_form.get("award", None))
            multiomics_form.setdefault("otherAward", context_form.get("otherAward", ""))

            metadata_submission.pop("contextForm", None)
        if metadata_submission.get("multiomicsForm", None):
            multiomics_form = metadata_submission.get("multiomicsForm", {})
            study_form = metadata_submission.get("studyForm", {})

            study_form.setdefault("alternativeNames", multiomics_form.get("alternativeNames", []))
            study_form.setdefault("GOLDStudyId", multiomics_form.get("GOLDStudyId", ""))
            study_form.setdefault("NCBIBioProjectId", multiomics_form.get("NCBIBioProjectId", ""))

            multiomics_form.pop("alternativeNames", None)
            multiomics_form.pop("GOLDStudyId", None)
            multiomics_form.pop("NCBIBioProjectId", None)
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

        if metadata_submission.get("multiomicsForm", None):
            multiomics_form = metadata_submission.get("multiomicsForm", {})
            context_form = {}

            context_form["datasetDoi"] = multiomics_form.get("datasetDoi", "")
            context_form["dataGenerated"] = multiomics_form.get("dataGenerated", None)
            context_form["facilityGenerated"] = multiomics_form.get("facilityGenerated", None)
            context_form["facilities"] = multiomics_form.get("facilities", [])
            context_form["award"] = multiomics_form.get("award", None)
            context_form["otherAward"] = multiomics_form.get("otherAward", "")

            metadata_submission["contextForm"] = context_form

        if metadata_submission.get("studyForm", None):
            study_form = metadata_submission.get("studyForm", {})
            multiomics_form = metadata_submission.get("multiomicsForm", {})

            multiomics_form["alternativeNames"] = study_form.get("alternativeNames", [])
            multiomics_form["GOLDStudyId"] = study_form.get("GOLDStudyId", "")
            multiomics_form["NCBIBioProjectId"] = study_form.get("NCBIBioProjectId", "")

            metadata_submission["multiomicsForm"] = multiomics_form

        mappings.append({"id": submission_metadata.id, "metadata_submission": metadata_submission})
    session.bulk_update_mappings(SubmissionMetadata, mappings)
    session.commit()
