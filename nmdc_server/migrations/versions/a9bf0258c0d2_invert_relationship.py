"""invert relationship

Revision ID: a9bf0258c0d2
Revises: 18e52534911c
Create Date: 2021-01-28 15:41:01.324587

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a9bf0258c0d2"
down_revision: Optional[str] = "18e52534911c"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.add_column("biosample", sa.Column("study_id", sa.String(), nullable=False))
    op.drop_constraint("fk_biosample_project_id_project", "biosample", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_biosample_study_id_study"), "biosample", "study", ["study_id"], ["id"]
    )
    op.drop_column("biosample", "project_id")
    op.add_column("project", sa.Column("biosample_id", sa.String(), nullable=True))
    op.drop_constraint("fk_project_study_id_study", "project", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_project_biosample_id_biosample"), "project", "biosample", ["biosample_id"], ["id"]
    )
    op.drop_column("project", "study_id")


def downgrade():
    op.add_column(
        "project", sa.Column("study_id", sa.VARCHAR(), autoincrement=False, nullable=False)
    )
    op.drop_constraint(op.f("fk_project_biosample_id_biosample"), "project", type_="foreignkey")
    op.create_foreign_key("fk_project_study_id_study", "project", "study", ["study_id"], ["id"])
    op.drop_column("project", "biosample_id")
    op.add_column(
        "biosample", sa.Column("project_id", sa.VARCHAR(), autoincrement=False, nullable=False)
    )
    op.drop_constraint(op.f("fk_biosample_study_id_study"), "biosample", type_="foreignkey")
    op.create_foreign_key(
        "fk_biosample_project_id_project", "biosample", "project", ["project_id"], ["id"]
    )
    op.drop_column("biosample", "study_id")
