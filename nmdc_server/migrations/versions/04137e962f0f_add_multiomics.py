"""add multiomics

Revision ID: 04137e962f0f
Revises: ef834f950de9
Create Date: 2021-05-16 00:22:03.125760

"""
from typing import Optional

import sqlalchemy as sa
from alembic import op

from nmdc_server.database import update_multiomics_sql

# revision identifiers, used by Alembic.
revision: str = "04137e962f0f"
down_revision: Optional[str] = "ef834f950de9"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.add_column(
        "biosample", sa.Column("multiomics", sa.Integer(), nullable=False, server_default="0")
    )
    op.execute(update_multiomics_sql)


def downgrade():
    op.drop_column("biosample", "multiomics")
