"""remove submission_metadata.templates

Revision ID: 2d175e58c0ae
Revises: 6031f61ff8c8
Create Date: 2026-06-01 20:26:20.291422

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2d175e58c0ae"
down_revision: Optional[str] = "6031f61ff8c8"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.drop_column("submission_metadata", "templates")


def downgrade():
    op.add_column(
        "submission_metadata",
        sa.Column(
            "templates",
            postgresql.JSONB(astext_type=sa.Text()),  # type: ignore[call-arg]
            autoincrement=False,
            nullable=True,
        ),
    )
