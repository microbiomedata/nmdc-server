"""add multiomics study

Revision ID: 79a0b5695e7d
Revises: 04137e962f0f
Create Date: 2021-05-24 12:05:09.339415

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa

from nmdc_server.database import update_multiomics_sql

# revision identifiers, used by Alembic.
revision: str = "79a0b5695e7d"
down_revision: Optional[str] = "04137e962f0f"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.add_column(
        "study", sa.Column("multiomics", sa.Integer(), nullable=False, server_default="0")
    )
    op.execute(update_multiomics_sql)


def downgrade():
    op.drop_column("study", "multiomics")
