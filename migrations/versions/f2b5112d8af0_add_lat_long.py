"""add lat-long

Revision ID: f2b5112d8af0
Revises:
Create Date: 2020-04-22 08:55:16.567119

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f2b5112d8af0"
down_revision: Optional[str] = None
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.add_column("biosample", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("biosample", sa.Column("longitude", sa.Float(), nullable=True))
    op.execute("update biosample set latitude = (annotations->>'latitude')::float")
    op.execute("update biosample set longitude = (annotations->>'longitude')::float")
    op.alter_column("biosample", "latitude", nullable=False)
    op.alter_column("biosample", "longitude", nullable=False)


def downgrade():
    op.drop_column("biosample", "longitude")
    op.drop_column("biosample", "latitude")
