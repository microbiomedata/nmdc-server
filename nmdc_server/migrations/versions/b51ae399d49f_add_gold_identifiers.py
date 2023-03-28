"""Add gold identifiers to study

Revision ID: b51ae399d49f
Revises: 7b9f5a789198
Create Date: 2023-03-27 15:38:36.490336

"""
from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b51ae399d49f"
down_revision: Optional[str] = "7b9f5a789198"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "study",
        sa.Column(
            "gold_study_identifiers",
            postgresql.JSONB(astext_type=sa.Text()),  # type: ignore
            nullable=True,
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("study", "gold_study_identifiers")
    # ### end Alembic commands ###
