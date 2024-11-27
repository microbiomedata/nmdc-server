"""Add field_notes_metadata column to submission_metadata

Revision ID: ceb93b48d6ae
Revises: 4aee1e10bb24
Create Date: 2024-11-18 21:49:50.640253

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "ceb93b48d6ae"
down_revision: Optional[str] = "4aee1e10bb24"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.add_column(
        "submission_metadata",
        sa.Column(
            "field_notes_metadata",
            postgresql.JSONB(astext_type=sa.Text()),  # type: ignore
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("submission_metadata", "field_notes_metadata")
