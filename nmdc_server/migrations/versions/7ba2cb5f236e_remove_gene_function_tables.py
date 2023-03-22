"""Remove tables used for aggregated gene functions during ingest

Revision ID: 7ba2cb5f236e
Revises: 11a7decdcc60
Create Date: 2023-03-20 22:10:29.149713

"""
from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "7ba2cb5f236e"
down_revision: Optional[str] = "11a7decdcc60"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("peptide_mga_gene_function")
    op.drop_table("metaproteomic_peptide")
    op.drop_table("mga_gene_function")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "peptide_mga_gene_function",
        sa.Column("id", postgresql.UUID(), autoincrement=False, nullable=False),
        sa.Column("subject", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column(
            "metaproteomic_peptide_id", postgresql.UUID(), autoincrement=False, nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["metaproteomic_peptide_id"],
            ["metaproteomic_peptide.id"],
            name="fk_peptide_mga_gene_function_metaproteomic_peptide_id_m_bb30",
        ),
        sa.ForeignKeyConstraint(
            ["subject"],
            ["mga_gene_function.subject"],
            name="fk_peptide_mga_gene_function_subject_mga_gene_function",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_peptide_mga_gene_function"),
    )
    op.create_table(
        "metaproteomic_peptide",
        sa.Column("id", postgresql.UUID(), autoincrement=False, nullable=False),
        sa.Column("metaproteomic_analysis_id", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("peptide_sequence", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("peptide_sum_masic_abundance", sa.BIGINT(), autoincrement=False, nullable=False),
        sa.Column("peptide_spectral_count", sa.BIGINT(), autoincrement=False, nullable=False),
        sa.Column("best_protein", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column(
            "min_q_value",
            postgresql.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["best_protein"],
            ["mga_gene_function.subject"],
            name="fk_metaproteomic_peptide_best_protein_mga_gene_function",
        ),
        sa.ForeignKeyConstraint(
            ["metaproteomic_analysis_id"],
            ["metaproteomic_analysis.id"],
            name="fk_metaproteomic_peptide_metaproteomic_analysis_id_meta_0290",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_metaproteomic_peptide"),
    )
    op.create_table(
        "mga_gene_function",
        sa.Column("id", postgresql.UUID(), autoincrement=False, nullable=False),
        sa.Column("metagenome_annotation_id", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("gene_function_id", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("subject", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["gene_function_id"],
            ["gene_function.id"],
            name="fk_mga_gene_function_gene_function_id_gene_function",
        ),
        sa.ForeignKeyConstraint(
            ["metagenome_annotation_id"],
            ["metagenome_annotation.id"],
            name="fk_mga_gene_function_metagenome_annotation_id_metagenom_d51d",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_mga_gene_function"),
        sa.UniqueConstraint("subject", name="uq_mga_gene_function_subject"),
    )
    # ### end Alembic commands ###