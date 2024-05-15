"""Create authorization_code table

Revision ID: 6cdad9ad6543
Revises: 60fef2166c84
Create Date: 2024-05-10 21:36:27.612777

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "6cdad9ad6543"
down_revision: Optional[str] = "60fef2166c84"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.create_table(
        "authorization_code",
        sa.Column("code", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("redirect_uri", sa.String(), nullable=False),
        sa.Column("exchanged", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user_logins.id"], name=op.f("fk_authorization_code_user_id_user_logins")
        ),
        sa.PrimaryKeyConstraint("code", name=op.f("pk_authorization_code")),
    )


def downgrade():
    op.drop_table("authorization_code")
