"""denorm gene function

Revision ID: 7057e7745ce6
Revises: 15fee92ce478
Create Date: 2021-02-15 15:27:05.787714

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7057e7745ce6"
down_revision: Optional[str] = "15fee92ce478"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.create_table(
        "metap_gene_function_aggregation",
        sa.Column("metaproteomic_analysis_id", sa.String(), nullable=False),
        sa.Column("gene_function_id", sa.String(), nullable=False),
        sa.Column("count", sa.BigInteger(), nullable=False),
        sa.Column("best_protein", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["gene_function_id"],
            ["gene_function.id"],
            name=op.f("fk_metap_gene_function_aggregation_gene_function_id_gene_function"),
        ),
        sa.ForeignKeyConstraint(
            ["metaproteomic_analysis_id"],
            ["metaproteomic_analysis.id"],
            name=op.f(
                "fk_metap_gene_function_aggregation_"
                "metaproteomic_analysis_id_metaproteomic_analysis"
            ),
        ),
        sa.PrimaryKeyConstraint(
            "metaproteomic_analysis_id",
            "gene_function_id",
            name=op.f("pk_metap_gene_function_aggregation"),
        ),
    )
    op.create_table(
        "mga_gene_function_aggregation",
        sa.Column("metagenome_annotation_id", sa.String(), nullable=False),
        sa.Column("gene_function_id", sa.String(), nullable=False),
        sa.Column("count", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["gene_function_id"],
            ["gene_function.id"],
            name=op.f("fk_mga_gene_function_aggregation_gene_function_id_gene_function"),
        ),
        sa.ForeignKeyConstraint(
            ["metagenome_annotation_id"],
            ["metagenome_annotation.id"],
            name=op.f(
                "fk_mga_gene_function_aggregation_metagenome_annotation_id_metagenome_annotation"
            ),
        ),
        sa.PrimaryKeyConstraint(
            "metagenome_annotation_id",
            "gene_function_id",
            name=op.f("pk_mga_gene_function_aggregation"),
        ),
    )


def downgrade():
    op.drop_table("mga_gene_function_aggregation")
    op.drop_table("metap_gene_function_aggregation")
