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
            multiomics_form = metadata_submission.get("multiOmicsForm", {})

            # Copy values of fields that moved from contextForm to multiOmicsForm
            multiomics_form.setdefault("award", context_form.get("award", None))
            multiomics_form.setdefault("awardDois", context_form.get("awardDois", None))
            multiomics_form.setdefault("dataGenerated", context_form.get("dataGenerated", None))
            multiomics_form.setdefault("facilities", context_form.get("facilities", None))
            multiomics_form.setdefault(
                "facilityGenerated", context_form.get("facilityGenerated", None)
            )
            multiomics_form.setdefault("otherAward", context_form.get("otherAward", None))
            multiomics_form.setdefault("ship", context_form.get("ship", None))
            multiomics_form.setdefault("unknownDoi", context_form.get("unknownDoi", None))

            # Remove the obsoleted contextForm
            metadata_submission.pop("contextForm", None)

            # Infer the value of the new `doe` field on the multiOmicsForm. This field captures whether samples will be
            # submitted to a DOE user facility, if data has not already been generated for them.
            data_generated = multiomics_form.get("dataGenerated")
            facilities = multiomics_form.get("facilities", [])
            omics_processing_types = multiomics_form.get("omicsProcessingTypes", [])
            if data_generated == False and len(facilities) > 0:
                multiomics_form["doe"] = True
            elif data_generated == False and any(t in omics_processing_types for t in ["mg", "mt", "mp", "mb", "nom"]):
                multiomics_form["doe"] = False

        if metadata_submission.get("multiOmicsForm", None):
            multiomics_form = metadata_submission.get("multiOmicsForm", {})
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

        if metadata_submission.get("multiOmicsForm", None):
            multiomics_form = metadata_submission.get("multiOmicsForm", {})
            context_form = {}

            context_form["award"] = multiomics_form.get("award", None)
            context_form["awardDois"] = multiomics_form.get("awardDois", None)
            context_form["dataGenerated"] = multiomics_form.get("dataGenerated", None)
            context_form["facilities"] = multiomics_form.get("facilities", [])
            context_form["facilityGenerated"] = multiomics_form.get("facilityGenerated", None)
            context_form["otherAward"] = multiomics_form.get("otherAward", "")
            context_form["ship"] = multiomics_form.get("ship", None)
            context_form["unknownDoi"] = multiomics_form.get("unknownDoi", None)

            metadata_submission["contextForm"] = context_form

            multiomics_form.pop("doe", None)
        if metadata_submission.get("studyForm", None):
            study_form = metadata_submission.get("studyForm", {})
            multiomics_form = metadata_submission.get("multiOmicsForm", {})

            multiomics_form["alternativeNames"] = study_form.get("alternativeNames", [])
            multiomics_form["GOLDStudyId"] = study_form.get("GOLDStudyId", "")
            multiomics_form["NCBIBioProjectId"] = study_form.get("NCBIBioProjectId", "")

            metadata_submission["multiOmicsForm"] = multiomics_form

        mappings.append({"id": submission_metadata.id, "metadata_submission": metadata_submission})
    session.bulk_update_mappings(SubmissionMetadata, mappings)
    session.commit()
