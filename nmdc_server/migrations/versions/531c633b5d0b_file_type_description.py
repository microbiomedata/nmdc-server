"""file type description


Revision ID: 531c633b5d0b
Revises: 0f5df87fca3a
Create Date: 2021-06-30 16:56:11.573187

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "531c633b5d0b"
down_revision: Optional[str] = "0f5df87fca3a"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.add_column("data_object", sa.Column("file_type_description", sa.String(), nullable=True))


def downgrade():
    op.drop_column("data_object", "file_type_description")
