"""metap peptide

Revision ID: 0464d245742c
Revises: 5aa75e4c1cad
Create Date: 2021-01-29 20:47:29.365838

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0464d245742c"
down_revision: Optional[str] = "5aa75e4c1cad"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.create_unique_constraint(
        op.f("uq_mga_gene_function_subject"), "mga_gene_function", ["subject"]
    )
    op.create_table(
        "metaproteomic_peptide",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metaproteomic_analysis_id", sa.String(), nullable=False),
        sa.Column("peptide_sequence", sa.String(), nullable=False),
        sa.Column("peptide_sum_masic_abundance", sa.BigInteger(), nullable=False),
        sa.Column("peptide_spectral_count", sa.BigInteger(), nullable=False),
        sa.Column("best_protein", sa.String(), nullable=False),
        sa.Column("min_q_value", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["best_protein"],
            ["mga_gene_function.subject"],
            name=op.f("fk_metaproteomic_peptide_best_protein_mga_gene_function"),
        ),
        sa.ForeignKeyConstraint(
            ["metaproteomic_analysis_id"],
            ["metaproteomic_analysis.id"],
            name=op.f("fk_metaproteomic_peptide_metaproteomic_analysis_id_metaproteomic_analysis"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_metaproteomic_peptide")),
    )
    op.create_table(
        "peptide_mga_gene_function",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("metaproteomic_peptide_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["metaproteomic_peptide_id"],
            ["metaproteomic_peptide.id"],
            name=op.f(
                "fk_peptide_mga_gene_function_metaproteomic_peptide_id_metaproteomic_peptide"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["subject"],
            ["mga_gene_function.subject"],
            name=op.f("fk_peptide_mga_gene_function_subject_mga_gene_function"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_peptide_mga_gene_function")),
    )


def downgrade():
    op.drop_table("peptide_mga_gene_function")
    op.drop_table("metaproteomic_peptide")
    op.drop_constraint(op.f("uq_mga_gene_function_subject"), "mga_gene_function", type_="unique")
