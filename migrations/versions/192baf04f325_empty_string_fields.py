"""empty string fields

Revision ID: 192baf04f325
Revises: 475bed7659be
Create Date: 2020-05-06 09:16:22.749953

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "192baf04f325"
down_revision: Optional[str] = "475bed7659be"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.execute("update study set gold_description = '' where gold_description is null")
    op.execute("update study set gold_name = '' where gold_name is null")
    op.execute("update study set scientific_objective = '' where scientific_objective is null")
    op.alter_column("study", "gold_description", existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column("study", "gold_name", existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column("study", "scientific_objective", existing_type=sa.VARCHAR(), nullable=False)


def downgrade():
    op.alter_column("study", "scientific_objective", existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column("study", "gold_name", existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column("study", "gold_description", existing_type=sa.VARCHAR(), nullable=True)
