"""add file downloads

Revision ID: 68a0445e19bf
Revises: e66a8305a730
Create Date: 2021-01-27 15:03:48.125215

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "68a0445e19bf"
down_revision: Optional[str] = "e66a8305a730"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.create_table(
        "file_download",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("data_object_id", sa.String(), nullable=False),
        sa.Column("ip", sa.String(), nullable=False),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("orcid", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["data_object_id"],
            ["data_object.id"],
            name=op.f("fk_file_download_data_object_id_data_object"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_file_download")),
    )


def downgrade():
    op.drop_constraint(op.f("uq_envo_ancestor_id"), "envo_ancestor", type_="unique")
    op.drop_table("file_download")
