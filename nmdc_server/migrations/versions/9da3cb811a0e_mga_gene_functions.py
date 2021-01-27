"""mga gene functions

Revision ID: 9da3cb811a0e
Revises: 8f03f0fac12b
Create Date: 2021-01-20 10:29:16.150426

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9da3cb811a0e"
down_revision: Optional[str] = "8f03f0fac12b"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.create_table(
        "gene_function",
        sa.Column("id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_gene_function")),
    )
    op.create_table(
        "mga_gene_function",
        sa.Column("metagenome_annotation_id", sa.String(), nullable=False),
        sa.Column("gene_function_id", sa.String(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["gene_function_id"],
            ["gene_function.id"],
            name=op.f("fk_mga_gene_function_gene_function_id_gene_function"),
        ),
        sa.ForeignKeyConstraint(
            ["metagenome_annotation_id"],
            ["metagenome_annotation.id"],
            name=op.f("fk_mga_gene_function_metagenome_annotation_id_metagenome_annotation"),
        ),
        sa.PrimaryKeyConstraint(
            "metagenome_annotation_id", "gene_function_id", name=op.f("pk_mga_gene_function")
        ),
    )
    op.create_unique_constraint(op.f("uq_envo_ancestor_id"), "envo_ancestor", ["id", "ancestor_id"])


def downgrade():
    op.drop_constraint(op.f("uq_envo_ancestor_id"), "envo_ancestor", type_="unique")
    op.drop_table("mga_gene_function")
    op.drop_table("gene_function")
