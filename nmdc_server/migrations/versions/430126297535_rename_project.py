"""rename project

Revision ID: 430126297535
Revises: f1cd153d1a16
Create Date: 2021-04-07 09:18:32.221455

"""
from typing import Optional

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "430126297535"
down_revision: Optional[str] = "f1cd153d1a16"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None

rename_fk_tables = [
    "data_object",
    "mags_analysis",
    "metabolomics_analysis",
    "metagenome_annotation",
    "metagenome_assembly",
    "metaproteomic_analysis",
    "nom_analysis",
    "read_based_analysis",
    "reads_qc",
]


def upgrade():
    op.rename_table("project_output_association", "omics_processing_output_association")
    op.rename_table("project", "omics_processing")

    for table in rename_fk_tables:
        op.alter_column(table, "project_id", new_column_name="omics_processing_id")


def downgrade():
    pass
