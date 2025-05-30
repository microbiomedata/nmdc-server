"""Add tables to store COG and PFAM terms

Separate these from the existing KEGG terms to allow
for more specific searches.

Revision ID: d89192564855
Revises: 224db8f7e8df
Create Date: 2024-10-09 20:08:45.656007

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d89192564855"
down_revision: Optional[str] = "224db8f7e8df"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "cog_term_text",
        sa.Column("term", sa.String(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("term", name=op.f("pk_cog_term_text")),
    )
    op.create_table(
        "pfam_term_text",
        sa.Column("term", sa.String(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("term", name=op.f("pk_pfam_term_text")),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("pfam_term_text")
    op.drop_table("cog_term_text")
    # ### end Alembic commands ###
