"""Add expired column to bulk_download table

Revision ID: 60fef2166c84
Revises: 89e8f6a21c8d
Create Date: 2024-05-03 22:35:35.842031

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "60fef2166c84"
down_revision: Optional[str] = "89e8f6a21c8d"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # Add new expired column to bulk_download table, false for new records
    op.add_column(
        "bulk_download",
        sa.Column("expired", sa.Boolean(), nullable=False, server_default=sa.sql.False_()),
    )

    # Consider any existing bulk downloads to be expired
    op.execute("UPDATE bulk_download SET expired = true")


def downgrade():
    op.drop_column("bulk_download", "expired")
