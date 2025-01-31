"""Add nmdc_edge as a source_client value

Revision ID: 4aee1e10bb24
Revises: b22c459110a0
Create Date: 2024-11-26 19:16:09.105692

"""

from typing import Optional

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4aee1e10bb24"
down_revision: Optional[str] = "b22c459110a0"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.execute("ALTER TYPE submissionsourceclient ADD VALUE 'nmdc_edge'")


def downgrade():
    op.execute("ALTER TYPE submissionsourceclient DROP VALUE 'nmdc_edge'")
