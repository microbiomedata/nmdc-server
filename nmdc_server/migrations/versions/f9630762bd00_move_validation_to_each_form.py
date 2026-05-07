"""This migration moves validation from the `validationState` form field to each individual form, so that we can track validation state separately for each form.
This is in preparation for the upcoming addition of having multiple sample sets per submission.

Revision ID: f9630762bd00
Revises: 6375d651d0b6
Create Date: 2026-05-07 18:56:05.537522

"""
from __future__ import annotations

from typing import Optional
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base

# revision identifiers, used by Alembic.
revision: str = "f9630762bd00"
down_revision: Optional[str] = "6375d651d0b6"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None

Base = declarative_base()


class SubmissionMetadata(Base):
    __tablename__ = "submission_metadata"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    metadata_submission = Column(JSONB, nullable=False)


def _ensure_dict(v):
    return v if isinstance(v, dict) else {}


def _ensure_list(v):
    return v if isinstance(v, list) else []


def upgrade():
    """
    Moves old validationState.* into per-form _validation fields.
    Ensures _validation is present on all new forms
    """
    connection = op.get_bind()
    session = sa.orm.Session(bind=connection)

    submissions = session.query(SubmissionMetadata).yield_per(2000)
    for row in submissions:
        ms = _ensure_dict(row.metadata_submission)

        address_form = _ensure_dict(ms.get("addressForm"))
        package_name = _ensure_list(ms.get("packageName"))
        templates = _ensure_list(ms.get("templates"))
        study_form = _ensure_dict(ms.get("studyForm"))
        multiomics_form = _ensure_dict(ms.get("multiOmicsForm"))
        sample_data = ms.get("sampleData")  # keep as-is

        validation_state = _ensure_dict(ms.get("validationState"))

        # ALWAYS set per-form validation lists (empty list if missing)
        study_form["_validation"] = _ensure_list(validation_state.get("studyForm"))
        multiomics_form["_validation"] = _ensure_list(validation_state.get("multiOmicsForm"))

        sender_shipping_info_form = dict(address_form)
        sender_shipping_info_form["_validation"] = _ensure_list(
            validation_state.get("senderShippingInfoForm")
        )

        sample_environment_form = {
            "packageName": package_name,
            "_validation": _ensure_list(validation_state.get("sampleEnvironmentForm")),
        }

        # sampleData becomes an object with {data, _validation}
        sample_metadata_validation = validation_state.get("sampleMetadata")
        new_sample_data = {"data": sample_data}
        if isinstance(sample_metadata_validation, dict):
            new_sample_data["_validation"] = sample_metadata_validation
        else:
            # if old value missing, backfill an empty validation state object
            new_sample_data["_validation"] = {"invalidCells": {}, "tabsValidated": {}}

        new_ms = dict(ms)
        # Add/overwrite the new shape keys
        new_ms["sampleEnvironmentForm"] = sample_environment_form
        new_ms["senderShippingInfoForm"] = sender_shipping_info_form
        new_ms["templates"] = templates
        new_ms["studyForm"] = study_form
        new_ms["multiOmicsForm"] = multiomics_form
        new_ms["sampleData"] = new_sample_data

        # Remove only the old keys that are no longer part of the new schema
        new_ms.pop("packageName", None)
        new_ms.pop("addressForm", None)
        new_ms.pop("validationState", None)

        row.metadata_submission = new_ms

    session.commit()


def downgrade():
    """
    Reconstructs old shape and puts per-form _validation back into validationState,
    while preserving any extra/unknown keys on metadata_submission.
    """
    connection = op.get_bind()
    session = sa.orm.Session(bind=connection)

    submissions = session.query(SubmissionMetadata).yield_per(2000)
    for row in submissions:
        ms = _ensure_dict(row.metadata_submission)

        sample_env_form = _ensure_dict(ms.get("sampleEnvironmentForm"))
        sender_ship_form = _ensure_dict(ms.get("senderShippingInfoForm"))
        templates = _ensure_list(ms.get("templates"))
        study_form = _ensure_dict(ms.get("studyForm"))
        multiomics_form = _ensure_dict(ms.get("multiOmicsForm"))
        sample_data_obj = _ensure_dict(ms.get("sampleData"))

        package_name = _ensure_list(sample_env_form.get("packageName"))

        # Old addressForm is senderShippingInfoForm without _validation
        address_form = dict(sender_ship_form)
        address_form.pop("_validation", None)

        # Rebuild validationState (ensure lists are lists)
        validation_state = {
            "studyForm": _ensure_list(study_form.get("_validation")),
            "multiOmicsForm": _ensure_list(multiomics_form.get("_validation")),
            "sampleEnvironmentForm": _ensure_list(sample_env_form.get("_validation")),
            "senderShippingInfoForm": _ensure_list(sender_ship_form.get("_validation")),
            "sampleMetadata": sample_data_obj.get("_validation")
            or {"invalidCells": {}, "tabsValidated": {}},
        }

        # Strip per-form _validation for old shape
        study_form_old = dict(study_form)
        study_form_old.pop("_validation", None)

        multiomics_form_old = dict(multiomics_form)
        multiomics_form_old.pop("_validation", None)

        old_sample_data = sample_data_obj.get("data")

        # Mutate in-place to preserve unknown/extra keys
        new_ms = dict(ms)

        # Add/overwrite old-shape keys
        new_ms["packageName"] = package_name
        new_ms["addressForm"] = address_form
        new_ms["templates"] = templates
        new_ms["studyForm"] = study_form_old
        new_ms["multiOmicsForm"] = multiomics_form_old
        new_ms["sampleData"] = old_sample_data
        new_ms["validationState"] = validation_state

        # Remove only the new-shape keys
        new_ms.pop("sampleEnvironmentForm", None)
        new_ms.pop("senderShippingInfoForm", None)

        row.metadata_submission = new_ms

    session.commit()
