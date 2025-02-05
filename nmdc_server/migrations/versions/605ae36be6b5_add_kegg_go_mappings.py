"""Add KEGG/GO mappings

Revision ID: 605ae36be6b5
Revises: ceb93b48d6ae
Create Date: 2024-11-25 21:21:57.310993

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "605ae36be6b5"
down_revision: Optional[str] = "ceb93b48d6ae"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "go_term_to_kegg_ortholog",
        sa.Column("term", sa.String(), nullable=False),
        sa.Column("kegg_term", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("term", "kegg_term", name=op.f("pk_go_term_to_kegg_ortholog")),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("go_term_to_kegg_ortholog")
    # ### end Alembic commands ###
