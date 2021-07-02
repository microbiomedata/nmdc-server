"""optional doi

Revision ID: 0f5df87fca3a
Revises: 1f47b94a6692
Create Date: 2021-06-30 15:10:09.400806

"""
from typing import Optional

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0f5df87fca3a"
down_revision: Optional[str] = "1f47b94a6692"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.alter_column("study", "doi", existing_type=sa.VARCHAR(), nullable=True)


def downgrade():
    op.alter_column("study", "doi", existing_type=sa.VARCHAR(), nullable=False)
