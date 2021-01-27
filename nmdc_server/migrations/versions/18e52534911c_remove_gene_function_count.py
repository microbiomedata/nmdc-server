"""remove gene function count

Revision ID: 18e52534911c
Revises: 68a0445e19bf
Create Date: 2021-01-27 15:54:00.080993

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "18e52534911c"
down_revision: Optional[str] = "68a0445e19bf"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.drop_table("mga_gene_function")
    op.create_table(
        "mga_gene_function",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metagenome_annotation_id", sa.String(), nullable=False),
        sa.Column("gene_function_id", sa.String(), nullable=False),
        sa.Column("subject", sa.String(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_mga_gene_function")),
    )


def downgrade():
    op.drop_table("mga_gene_function")
