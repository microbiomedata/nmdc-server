"""Remove `has_calibration` column from metabolomics

Revision ID: 9ba1b6ff84e9
Revises: d89192564855
Create Date: 2024-11-15 14:44:30.209283

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9ba1b6ff84e9"
down_revision: Optional[str] = "d89192564855"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("metabolomics_analysis", "has_calibration")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "metabolomics_analysis",
        sa.Column(
            "has_calibration",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=False,
            default="",
            server_default="",
        ),
    )
    # ### end Alembic commands ###
