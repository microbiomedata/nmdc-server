"""nullable study

Revision ID: e2df18f14429
Revises: a9bf0258c0d2
Create Date: 2021-01-28 17:24:48.950907

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e2df18f14429"
down_revision: Optional[str] = "a9bf0258c0d2"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.add_column("project", sa.Column("study_id", sa.String(), nullable=True))
    op.create_foreign_key(
        op.f("fk_project_study_id_study"), "project", "study", ["study_id"], ["id"]
    )


def downgrade():
    op.drop_constraint(op.f("fk_project_study_id_study"), "project", type_="foreignkey")
    op.drop_column("project", "study_id")
