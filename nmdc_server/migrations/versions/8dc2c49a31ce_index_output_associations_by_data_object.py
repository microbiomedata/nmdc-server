"""Index output associations by data object.

Revision ID: 8dc2c49a31ce
Revises: da7be44d437c
"""

from typing import Optional

from alembic import op

revision: str = "8dc2c49a31ce"
down_revision: Optional[str] = "da7be44d437c"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None

OUTPUT_ASSOCIATION_TABLES = (
    "omics_processing",
    "reads_qc",
    "metagenome_assembly",
    "metatranscriptome_assembly",
    "metagenome_annotation",
    "metatranscriptome_annotation",
    "metaproteomic_analysis",
    "mags_analysis",
    "read_based_analysis",
    "nom_analysis",
    "metabolomics_analysis",
    "metatranscriptome",
)


def upgrade() -> None:
    for table_prefix in OUTPUT_ASSOCIATION_TABLES:
        op.create_index(
            f"ix_{table_prefix}_output_dobj_id",
            f"{table_prefix}_output_association",
            ["data_object_id"],
        )


def downgrade() -> None:
    for table_prefix in reversed(OUTPUT_ASSOCIATION_TABLES):
        op.drop_index(
            f"ix_{table_prefix}_output_dobj_id",
            table_name=f"{table_prefix}_output_association",
        )
