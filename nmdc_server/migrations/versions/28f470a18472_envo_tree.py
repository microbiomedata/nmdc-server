"""empty message

Revision ID: 28f470a18472
Revises: cab1403436ff
Create Date: 2021-08-03 14:28:03.692707

"""
from typing import Optional

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "28f470a18472"
down_revision: Optional[str] = "cab1403436ff"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "envo_tree",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("parent_id", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_envo_tree")),
    )
    op.create_index(op.f("ix_envo_tree_parent_id"), "envo_tree", ["parent_id"], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_envo_tree_parent_id"), table_name="envo_tree")
    op.drop_table("envo_tree")
    # ### end Alembic commands ###
