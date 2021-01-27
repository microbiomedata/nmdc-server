"""data object url

Revision ID: f8917d5479b8
Revises: 4b85f324a361
Create Date: 2021-01-26 13:22:23.189044

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f8917d5479b8"
down_revision: Optional[str] = "4b85f324a361"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.add_column("data_object", sa.Column("url", sa.String(), nullable=True))


def downgrade():
    op.drop_column("data_object", "url")
