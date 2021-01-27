"""optional biosample fields

Revision ID: e66a8305a730
Revises: f8917d5479b8
Create Date: 2021-01-26 15:25:14.353940

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e66a8305a730"
down_revision: Optional[str] = "f8917d5479b8"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.alter_column("biosample", "add_date", existing_type=postgresql.TIMESTAMP(), nullable=True)
    op.alter_column("biosample", "ecosystem", existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column("biosample", "ecosystem_category", existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column("biosample", "ecosystem_subtype", existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column("biosample", "ecosystem_type", existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column("biosample", "mod_date", existing_type=postgresql.TIMESTAMP(), nullable=True)
    op.alter_column("biosample", "specific_ecosystem", existing_type=sa.VARCHAR(), nullable=True)


def downgrade():
    op.alter_column("biosample", "specific_ecosystem", existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column("biosample", "mod_date", existing_type=postgresql.TIMESTAMP(), nullable=False)
    op.alter_column("biosample", "ecosystem_type", existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column("biosample", "ecosystem_subtype", existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column("biosample", "ecosystem_category", existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column("biosample", "ecosystem", existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column("biosample", "add_date", existing_type=postgresql.TIMESTAMP(), nullable=False)
