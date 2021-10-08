"""empty message

Revision ID: dddccd150962
Revises: cc01c50edacd
Create Date: 2021-10-08 18:38:45.027841

"""
from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "dddccd150962"
down_revision: Optional[str] = "cc01c50edacd"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "study",
        sa.Column("ess_dive_datasets", postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # type: ignore
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("study", "ess_dive_datasets")
    # ### end Alembic commands ###
