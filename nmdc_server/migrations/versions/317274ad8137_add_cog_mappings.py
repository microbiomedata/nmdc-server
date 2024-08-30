"""Add COG mappings

Revision ID: 317274ad8137
Revises: 0ff690fb929d
Create Date: 2024-08-30 20:13:12.480955

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "317274ad8137"
down_revision: Optional[str] = "0ff690fb929d"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "cog_term_to_function",
        sa.Column("term", sa.String(), nullable=False),
        sa.Column("function", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("term", "function", name=op.f("pk_cog_term_to_function")),
    )
    op.create_index(
        op.f("ix_cog_term_to_function_function"), "cog_term_to_function", ["function"], unique=False
    )
    op.create_table(
        "cog_term_to_pathway",
        sa.Column("term", sa.String(), nullable=False),
        sa.Column("pathway", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("term", "pathway", name=op.f("pk_cog_term_to_pathway")),
    )
    op.create_index(
        op.f("ix_cog_term_to_pathway_pathway"), "cog_term_to_pathway", ["pathway"], unique=False
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_cog_term_to_pathway_pathway"), table_name="cog_term_to_pathway")
    op.drop_table("cog_term_to_pathway")
    op.drop_index(op.f("ix_cog_term_to_function_function"), table_name="cog_term_to_function")
    op.drop_table("cog_term_to_function")
    # ### end Alembic commands ###
