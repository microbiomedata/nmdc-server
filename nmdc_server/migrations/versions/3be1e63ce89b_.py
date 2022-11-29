"""empty message

Revision ID: 3be1e63ce89b
Revises: ae7a3eba08c5, 86f42a05252b
Create Date: 2022-11-29 11:26:29.357442

"""
from typing import Optional, Tuple

# revision identifiers, used by Alembic.
revision: str = "3be1e63ce89b"
down_revision: Tuple[str, str] = ("ae7a3eba08c5", "86f42a05252b")
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    pass


def downgrade():
    pass
