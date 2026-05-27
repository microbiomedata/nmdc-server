"""add submission_sample_set table

Revision ID: 6274a27c66dd
Revises: f9630762bd00
Create Date: 2026-05-26 22:29:52.919275

"""

from typing import Optional
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import column, table

# revision identifiers, used by Alembic.
revision: str = "6274a27c66dd"
down_revision: Optional[str] = "f9630762bd00"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # Create new tables and columns.
    op.create_table(
        "submission_sample_set",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column("submission_metadata_id", postgresql.UUID(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("templates", postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # type: ignore[call-arg]
        sa.Column(
            "sample_environment_form", postgresql.JSONB(astext_type=sa.Text()), nullable=True  # type: ignore[call-arg]
        ),
        sa.Column(
            "sender_shipping_info_form", postgresql.JSONB(astext_type=sa.Text()), nullable=True  # type: ignore[call-arg]
        ),
        sa.Column("multi_omics_form", postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # type: ignore[call-arg]
        sa.Column("sample_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # type: ignore[call-arg]
        sa.ForeignKeyConstraint(
            ["submission_metadata_id"],
            ["submission_metadata.id"],
            name=op.f("fk_submission_sample_set_submission_metadata_id_submission_metadata"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_submission_sample_set")),
    )
    op.add_column(
        "submission_metadata",
        sa.Column("study_form", postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # type: ignore[call-arg]
    )

    # Define tables as they exist after new tables/columns have been added, but before old columns
    # have been removed, to allow for data migration.
    submission_metadata = table(
        "submission_metadata",
        column("id", postgresql.UUID),
        column("status", sa.String),
        column("metadata_submission", JSONB),
        column("study_form", JSONB),
    )
    submission_sample_set = table(
        "submission_sample_set",
        column("id", postgresql.UUID),
        column("submission_metadata_id", postgresql.UUID),
        column("status", sa.String),
        column("templates", JSONB),
        column("sample_environment_form", JSONB),
        column("sender_shipping_info_form", JSONB),
        column("multi_omics_form", JSONB),
        column("sample_data", JSONB),
    )

    connection = op.get_bind()
    submissions = connection.execute(
        sa.select(
            submission_metadata.c.id,  # type: ignore[arg-type]
            submission_metadata.c.status,
            submission_metadata.c.metadata_submission,  # type: ignore[arg-type]
        )
    )

    # For each existing submission, create a new submission_sample_set row with the relevant data
    # from the metadata_submission JSONB column and move the studyForm data to the new study_form
    # column in submission_metadata. Move the status from submission_metadata to submission_sample_set.
    for submission in submissions:
        metadata_submission = submission.metadata_submission
        if not isinstance(metadata_submission, dict):
            metadata_submission = {}

        connection.execute(
            submission_metadata.update()
            .where(submission_metadata.c.id == submission.id)
            .values(study_form=metadata_submission.get("studyForm"))
        )

        connection.execute(
            submission_sample_set.insert().values(
                id=uuid4(),
                submission_metadata_id=submission.id,
                status=submission.status,
                templates=metadata_submission.get("templates"),
                sample_environment_form=metadata_submission.get("sampleEnvironmentForm"),
                sender_shipping_info_form=metadata_submission.get("senderShippingInfoForm"),
                multi_omics_form=metadata_submission.get("multiOmicsForm"),
                sample_data=metadata_submission.get("sampleData"),
            )
        )

    # Remove old columns that have been split into the new submission_sample_set table.
    op.drop_column("submission_metadata", "metadata_submission")
    op.drop_column("submission_metadata", "status")


def downgrade():
    op.add_column(
        "submission_metadata",
        sa.Column(
            "metadata_submission",
            postgresql.JSONB(astext_type=sa.Text()),  # type: ignore[call-arg]
            nullable=False,
            default={},
        ),
    )
    op.add_column(
        "submission_metadata",
        sa.Column(
            "status",
            sa.String(),
            nullable=False,
            default="InProgress",
        ),
    )
    submission_metadata = table(
        "submission_metadata",
        column("id", postgresql.UUID),
        column("status", sa.String),
        column("metadata_submission", JSONB),
        column("study_form", JSONB),
    )
    submission_sample_set = table(
        "submission_sample_set",
        column("id", postgresql.UUID),
        column("submission_metadata_id", postgresql.UUID),
        column("status", sa.String),
        column("templates", JSONB),
        column("sample_environment_form", JSONB),
        column("sender_shipping_info_form", JSONB),
        column("multi_omics_form", JSONB),
        column("sample_data", JSONB),
    )

    connection = op.get_bind()
    sample_sets_by_submission_id = {
        sample_set.submission_metadata_id: sample_set
        for sample_set in connection.execute(sa.select(submission_sample_set))  # type: ignore[arg-type]
    }
    submissions = connection.execute(
        sa.select(
            submission_metadata.c.id,  # type: ignore[arg-type]
            submission_metadata.c.study_form,
        )
    )

    for submission in submissions:
        sample_set = sample_sets_by_submission_id.get(submission.id)
        metadata_submission = {
            "studyForm": submission.study_form if isinstance(submission.study_form, dict) else {},
            "templates": sample_set.templates if sample_set else None,
            "sampleEnvironmentForm": sample_set.sample_environment_form if sample_set else None,
            "senderShippingInfoForm": sample_set.sender_shipping_info_form if sample_set else None,
            "multiOmicsForm": sample_set.multi_omics_form if sample_set else None,
            "sampleData": sample_set.sample_data if sample_set else None,
        }
        status = sample_set.status if sample_set else "InProgress"

        connection.execute(
            submission_metadata.update()
            .where(submission_metadata.c.id == submission.id)
            .values(metadata_submission=metadata_submission, status=status)
        )

    op.drop_column("submission_metadata", "study_form")
    op.drop_table("submission_sample_set")
