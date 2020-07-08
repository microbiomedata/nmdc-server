"""join envo tables

Revision ID: af4f8dddfdd1
Revises: 4df378f8af6c
Create Date: 2020-07-08 13:43:59.920790

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "af4f8dddfdd1"
down_revision: Optional[str] = "4df378f8af6c"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.add_column("biosample", sa.Column("env_broad_scale_id", sa.String(), nullable=True))
    op.add_column("biosample", sa.Column("env_local_scale_id", sa.String(), nullable=True))
    op.add_column("biosample", sa.Column("env_medium_id", sa.String(), nullable=True))
    op.create_foreign_key(
        op.f("fk_biosample_env_broad_scale_id_envo_term"),
        "biosample",
        "envo_term",
        ["env_broad_scale_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_biosample_env_medium_id_envo_term"),
        "biosample",
        "envo_term",
        ["env_medium_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_biosample_env_local_scale_id_envo_term"),
        "biosample",
        "envo_term",
        ["env_local_scale_id"],
        ["id"],
    )
    op.drop_column("biosample", "env_medium")
    op.drop_column("biosample", "env_local_scale")
    op.drop_column("biosample", "env_broad_scale")


def downgrade():
    op.add_column(
        "biosample", sa.Column("env_broad_scale", sa.VARCHAR(), autoincrement=False, nullable=False)
    )
    op.add_column(
        "biosample", sa.Column("env_local_scale", sa.VARCHAR(), autoincrement=False, nullable=False)
    )
    op.add_column(
        "biosample", sa.Column("env_medium", sa.VARCHAR(), autoincrement=False, nullable=False)
    )
    op.drop_constraint(
        op.f("fk_biosample_env_local_scale_id_envo_term"), "biosample", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_biosample_env_medium_id_envo_term"), "biosample", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_biosample_env_broad_scale_id_envo_term"), "biosample", type_="foreignkey"
    )
    op.drop_column("biosample", "env_medium_id")
    op.drop_column("biosample", "env_local_scale_id")
    op.drop_column("biosample", "env_broad_scale_id")
