"""pi image

Revision ID: 1f47b94a6692
Revises: da4a0d10abcf
Create Date: 2021-06-30 10:43:48.267251

"""
from typing import Optional

from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1f47b94a6692"
down_revision: Optional[str] = "da4a0d10abcf"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.alter_column(
        "principal_investigator", "image", existing_type=postgresql.BYTEA(), nullable=True
    )


def downgrade():
    op.alter_column(
        "principal_investigator", "image", existing_type=postgresql.BYTEA(), nullable=False
    )
