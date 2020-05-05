"""add study fields

Revision ID: de2aa100425d
Revises: f2b5112d8af0
Create Date: 2020-05-05 08:56:15.336306

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "de2aa100425d"
down_revision: Optional[str] = "f2b5112d8af0"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.add_column("study", sa.Column("gold_description", sa.String(), nullable=True))
    op.add_column("study", sa.Column("gold_name", sa.String(), nullable=True))


def downgrade():
    op.drop_column("study", "gold_name")
    op.drop_column("study", "gold_description")
