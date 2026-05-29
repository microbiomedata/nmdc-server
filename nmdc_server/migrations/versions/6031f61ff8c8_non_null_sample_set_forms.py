"""non-null sample set forms

Revision ID: 6031f61ff8c8
Revises: 3ead3f3357a2
Create Date: 2026-05-29 19:57:32.886286

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "6031f61ff8c8"
down_revision: Optional[str] = "3ead3f3357a2"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.alter_column(
        "submission_sample_set",
        "templates",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),  # type: ignore[call-arg]
        nullable=False,
    )
    op.alter_column(
        "submission_sample_set",
        "sample_environment_form",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),  # type: ignore[call-arg]
        nullable=False,
    )
    op.alter_column(
        "submission_sample_set",
        "sender_shipping_info_form",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),  # type: ignore[call-arg]
        nullable=False,
    )
    op.alter_column(
        "submission_sample_set",
        "multi_omics_form",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),  # type: ignore[call-arg]
        nullable=False,
    )
    op.alter_column(
        "submission_sample_set",
        "sample_data",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),  # type: ignore[call-arg]
        nullable=False,
    )


def downgrade():
    op.alter_column(
        "submission_sample_set",
        "sample_data",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),  # type: ignore[call-arg]
        nullable=True,
    )
    op.alter_column(
        "submission_sample_set",
        "multi_omics_form",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),  # type: ignore[call-arg]
        nullable=True,
    )
    op.alter_column(
        "submission_sample_set",
        "sender_shipping_info_form",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),  # type: ignore[call-arg]
        nullable=True,
    )
    op.alter_column(
        "submission_sample_set",
        "sample_environment_form",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),  # type: ignore[call-arg]
        nullable=True,
    )
    op.alter_column(
        "submission_sample_set",
        "templates",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),  # type: ignore[call-arg]
        nullable=True,
    )
