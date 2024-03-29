"""Make file_size_bytes optional

Revision ID: dcc0a41b60af
Revises: b8f3bcb681a1
Create Date: 2023-07-12 21:28:22.917163

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "dcc0a41b60af"
down_revision: Optional[str] = "b8f3bcb681a1"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "data_object",
        "file_size_bytes",
        existing_type=sa.BIGINT(),
        nullable=True,
    )
    op.alter_column(
        "biosample",
        "latitude",
        existing_type=postgresql.DOUBLE_PRECISION(precision=53),
        nullable=True,
    )
    op.alter_column(
        "biosample",
        "longitude",
        existing_type=postgresql.DOUBLE_PRECISION(precision=53),
        nullable=True,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "data_object",
        "file_size_bytes",
        existing_type=sa.BIGINT(),
        nullable=False,
    )
    op.alter_column(
        "biosample",
        "latitude",
        existing_type=postgresql.DOUBLE_PRECISION(precision=53),
        nullable=False,
    )
    op.alter_column(
        "biosample",
        "longitude",
        existing_type=postgresql.DOUBLE_PRECISION(precision=53),
        nullable=False,
    )
    # ### end Alembic commands ###
