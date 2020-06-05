"""mixs schema

Revision ID: ff0a31bb7f64
Revises: 192baf04f325
Create Date: 2020-06-05 08:50:33.977449

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "ff0a31bb7f64"
down_revision: Optional[str] = "192baf04f325"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # need to reingest
    op.execute("delete from data_object")
    op.execute("delete from biosample")

    op.add_column(
        "biosample", sa.Column("alternate_identifiers", postgresql.JSONB(), nullable=False),
    )
    op.add_column("biosample", sa.Column("depth", sa.Float(), nullable=True))
    op.add_column("biosample", sa.Column("env_broad_scale", sa.String(), nullable=False))
    op.add_column("biosample", sa.Column("env_local_scale", sa.String(), nullable=False))
    op.add_column("biosample", sa.Column("env_medium", sa.String(), nullable=False))
    op.add_column(
        "data_object",
        sa.Column("alternate_identifiers", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "project",
        sa.Column("alternate_identifiers", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "study",
        sa.Column("alternate_identifiers", postgresql.JSONB(), nullable=False, server_default="[]"),
    )


def downgrade():
    op.drop_column("study", "alternate_identifiers")
    op.drop_column("project", "alternate_identifiers")
    op.drop_column("data_object", "alternate_identifiers")
    op.drop_column("biosample", "env_medium")
    op.drop_column("biosample", "env_local_scale")
    op.drop_column("biosample", "env_broad_scale")
    op.drop_column("biosample", "depth")
    op.drop_column("biosample", "alternate_identifiers")
