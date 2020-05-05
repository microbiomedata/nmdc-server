"""add study objective

Revision ID: 475bed7659be
Revises: d3136b720704
Create Date: 2020-05-05 14:54:30.297013

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "475bed7659be"
down_revision: Optional[str] = "d3136b720704"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.add_column("study", sa.Column("scientific_objective", sa.String(), nullable=True))


def downgrade():
    op.drop_column("study", "scientific_objective")
