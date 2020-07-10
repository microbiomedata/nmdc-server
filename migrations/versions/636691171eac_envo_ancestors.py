"""envo ancestors

Revision ID: 636691171eac
Revises: af4f8dddfdd1
Create Date: 2020-07-10 16:14:58.514615

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "636691171eac"
down_revision: Optional[str] = "af4f8dddfdd1"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.create_table(
        "envo_ancestor",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("ancestor_id", sa.String(), nullable=False),
        sa.Column("direct", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["ancestor_id"], ["envo_term.id"], name=op.f("fk_envo_ancestor_ancestor_id_envo_term")
        ),
        sa.ForeignKeyConstraint(
            ["id"], ["envo_term.id"], name=op.f("fk_envo_ancestor_id_envo_term")
        ),
        sa.PrimaryKeyConstraint("id", "ancestor_id", name=op.f("pk_envo_ancestor")),
        sa.UniqueConstraint("id", "ancestor_id", name=op.f("uq_envo_ancestor_id")),
    )


def downgrade():
    op.drop_table("envo_ancestor")
