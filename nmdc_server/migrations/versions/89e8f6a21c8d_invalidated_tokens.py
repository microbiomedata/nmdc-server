"""Add invalidated_token table

Revision ID: 89e8f6a21c8d
Revises: b4b234bd55cf
Create Date: 2024-04-19 18:33:18.632583

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "89e8f6a21c8d"
down_revision: Optional[str] = "b4b234bd55cf"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.create_table(
        "invalidated_token",
        sa.Column("token", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("token", name=op.f("pk_invalidated_token")),
    )


def downgrade():
    op.drop_table("invalidated_token")
