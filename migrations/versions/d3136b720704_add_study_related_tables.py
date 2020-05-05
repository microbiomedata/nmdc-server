"""add study related tables

Revision ID: d3136b720704
Revises: de2aa100425d
Create Date: 2020-05-05 13:40:13.076465

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d3136b720704"
down_revision: Optional[str] = "de2aa100425d"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.create_table(
        "publication",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column("doi", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_publication")),
        sa.UniqueConstraint("doi", name=op.f("uq_publication_doi")),
    )
    op.create_table(
        "website",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_website")),
        sa.UniqueConstraint("url", name=op.f("uq_website_url")),
    )
    op.create_table(
        "study_publication",
        sa.Column("study_id", sa.String(), nullable=False),
        sa.Column("publication_id", postgresql.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["publication_id"],
            ["publication.id"],
            name=op.f("fk_study_publication_publication_id_publication"),
        ),
        sa.ForeignKeyConstraint(
            ["study_id"], ["study.id"], name=op.f("fk_study_publication_study_id_study")
        ),
        sa.PrimaryKeyConstraint("study_id", "publication_id", name=op.f("pk_study_publication")),
    )
    op.create_table(
        "study_website",
        sa.Column("study_id", sa.String(), nullable=False),
        sa.Column("website_id", postgresql.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id"], ["study.id"], name=op.f("fk_study_website_study_id_study")
        ),
        sa.ForeignKeyConstraint(
            ["website_id"], ["website.id"], name=op.f("fk_study_website_website_id_website")
        ),
        sa.PrimaryKeyConstraint("study_id", "website_id", name=op.f("pk_study_website")),
    )


def downgrade():
    op.drop_table("study_website")
    op.drop_table("study_publication")
    op.drop_table("website")
    op.drop_table("publication")
