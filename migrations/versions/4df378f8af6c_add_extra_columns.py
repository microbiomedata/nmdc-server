"""add extra columns

Revision ID: 4df378f8af6c
Revises: 900d22d746e9
Create Date: 2020-07-01 11:10:26.434445

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4df378f8af6c"
down_revision: Optional[str] = "900d22d746e9"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.add_column("biosample", sa.Column("add_date", sa.DateTime(), nullable=False))
    op.add_column("biosample", sa.Column("mod_date", sa.DateTime(), nullable=False))
    op.add_column("data_object", sa.Column("file_size_bytes", sa.BigInteger(), nullable=False))
    op.add_column("project", sa.Column("add_date", sa.DateTime(), nullable=False))
    op.add_column("project", sa.Column("mod_date", sa.DateTime(), nullable=False))
    op.add_column("study", sa.Column("add_date", sa.DateTime(), nullable=False))
    op.add_column("study", sa.Column("mod_date", sa.DateTime(), nullable=False))


def downgrade():
    op.drop_column("study", "mod_date")
    op.drop_column("study", "add_date")
    op.drop_column("project", "mod_date")
    op.drop_column("project", "add_date")
    op.drop_column("data_object", "file_size_bytes")
    op.drop_column("biosample", "mod_date")
    op.drop_column("biosample", "add_date")
