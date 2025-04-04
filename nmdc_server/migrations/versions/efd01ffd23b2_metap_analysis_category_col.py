"""Add column for metaproteomics_analysis_category

Revision ID: efd01ffd23b2
Revises: c27777e272d3
Create Date: 2025-03-11 16:37:05.982101

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "efd01ffd23b2"
down_revision: Optional[str] = "c27777e272d3"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "metaproteomic_analysis",
        sa.Column(
            "metaproteomics_analysis_category",
            sa.String(),
            nullable=False,
            server_default="",
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("metaproteomic_analysis", "metaproteomics_analysis_category")
    # ### end Alembic commands ###
