"""empty message

Revision ID: 729a1c13fe30
Revises: 7e990d499034
Create Date: 2021-09-21 16:25:44.442280

"""
from typing import Optional

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "729a1c13fe30"
down_revision: Optional[str] = "7e990d499034"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "ko_term_text",
        sa.Column("term", sa.String(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("term", name=op.f("pk_ko_term_text")),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("ko_term_text")
    # ### end Alembic commands ###
