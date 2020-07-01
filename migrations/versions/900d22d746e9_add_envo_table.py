"""add envo table

Revision ID: 900d22d746e9
Revises: ff0a31bb7f64
Create Date: 2020-06-29 15:56:21.067979

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "900d22d746e9"
down_revision: Optional[str] = "ff0a31bb7f64"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.create_table(
        "envo_term",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),  # type: ignore
        sa.PrimaryKeyConstraint("id", name=op.f("pk_envo_term")),
    )


def downgrade():
    op.drop_table("envo_term")
