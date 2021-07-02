"""bulk download

Revision ID: 7f9314e44f22
Revises: 79a0b5695e7d
Create Date: 2021-06-14 08:32:03.669322

"""
from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "7f9314e44f22"
down_revision: Optional[str] = "79a0b5695e7d"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.create_table(
        "bulk_download",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("orcid", sa.String(), nullable=False),
        sa.Column("ip", sa.String(), nullable=False),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column(
            "conditions",
            postgresql.JSONB(astext_type=sa.Text()),  # type: ignore
            nullable=False,
        ),
        sa.Column(
            "filter",
            postgresql.JSONB(astext_type=sa.Text()),  # type: ignore
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_bulk_download")),
    )
    op.create_table(
        "bulk_download_data_object",
        sa.Column("bulk_download_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("data_object_id", sa.String(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["bulk_download_id"],
            ["bulk_download.id"],
            name=op.f("fk_bulk_download_data_object_bulk_download_id_bulk_download"),
        ),
        sa.ForeignKeyConstraint(
            ["data_object_id"],
            ["data_object.id"],
            name=op.f("fk_bulk_download_data_object_data_object_id_data_object"),
        ),
        sa.PrimaryKeyConstraint(
            "bulk_download_id", "data_object_id", name=op.f("pk_bulk_download_data_object")
        ),
    )
    op.add_column("data_object", sa.Column("file_type", sa.String(), nullable=True))


def downgrade():
    op.drop_column("data_object", "file_type")
    op.drop_table("bulk_download_data_object")
    op.drop_table("bulk_download")
