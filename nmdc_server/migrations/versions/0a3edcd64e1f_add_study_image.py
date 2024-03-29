"""Add image column to study model

Revision ID: 0a3edcd64e1f
Revises: 60b8a4b0c60e
Create Date: 2023-03-31 19:37:14.137698

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0a3edcd64e1f"
down_revision: Optional[str] = "60b8a4b0c60e"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("study", sa.Column("image", sa.LargeBinary(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("study", "image")
    # ### end Alembic commands ###
