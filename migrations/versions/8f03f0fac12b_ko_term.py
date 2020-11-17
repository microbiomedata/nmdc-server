"""ko term

Revision ID: 8f03f0fac12b
Revises: 
Create Date: 2020-11-17 08:35:22.792140

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8f03f0fac12b"
down_revision: Optional[str] = None
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "ko_term",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("count", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"], ["project.id"], name=op.f("fk_ko_term_project_id_project")
        ),
        sa.PrimaryKeyConstraint("id", "project_id", name=op.f("pk_ko_term")),
    )
    op.create_unique_constraint(op.f("uq_envo_ancestor_id"), "envo_ancestor", ["id", "ancestor_id"])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f("uq_envo_ancestor_id"), "envo_ancestor", type_="unique")
    op.drop_table("ko_term")
    # ### end Alembic commands ###
