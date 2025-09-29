"""update created on auth code

Revision ID: 9a0ff33a4e6b
Revises: 43fc92514a16
Create Date: 2025-09-04 17:57:09.179079

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9a0ff33a4e6b"
down_revision: Optional[str] = "43fc92514a16"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.alter_column(
        "authorization_code",
        "created",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
    )


def downgrade():
    op.alter_column(
        "authorization_code",
        "created",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
    )
