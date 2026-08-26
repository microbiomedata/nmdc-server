"""add lims export columns to submission_sample_set

Revision ID: b2c3d4e5f6a7
Revises: da7be44d437c
Create Date: 2026-08-26

Adds bookkeeping columns for the NMDC -> EMSL LIMS export:
  * lims_export_results (JSONB) -- per-sample send results returned by the LIMS receiver.
  * lims_exported_at   (timestamp) -- when the most recent export was attempted.
"""

from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "b2c3d4e5f6a7"
down_revision: Optional[str] = "da7be44d437c"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.add_column("submission_sample_set", sa.Column("lims_export_results", JSONB(), nullable=True))
    op.add_column("submission_sample_set", sa.Column("lims_exported_at", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("submission_sample_set", "lims_exported_at")
    op.drop_column("submission_sample_set", "lims_export_results")
