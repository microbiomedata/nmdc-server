"""add workflow type

Revision ID: da4a0d10abcf
Revises: c4d63f4206fb
Create Date: 2021-06-17 09:58:59.127673

"""
from typing import Optional

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "da4a0d10abcf"
down_revision: Optional[str] = "c4d63f4206fb"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None

workflow_type_map = {
    "reads_qc": "nmdc:ReadQCAnalysisActivity",
    "metagenome_assembly": "nmdc:MetagenomeAssembly",
    "metagenome_annotation": "nmdc:MetagenomeAnnotation",
    "metaproteomic_analysis": "nmdc:MetaProteomicAnalysis",
    "mags_analysis": "nmdc:MAGsAnalysisActivity",
    "read_based_analysis": "nmdc:ReadbasedAnalysis",
    "nom_analysis": "nmdc:NomAnalysisActivity",
    "metabolomics_analysis": "nmdc:MetabolomicsAnalysisActivity",
    "omics_processing": "nmdc:RawData",
}


def upgrade():
    op.add_column("data_object", sa.Column("workflow_type", sa.String(), nullable=True))

    for table, workflow in workflow_type_map.items():
        op.execute(
            f"""
            update data_object
            set workflow_type = '{workflow}'
            from (
                select d.id from
                data_object d
                join {table}_output_association a on d.id = a.data_object_id
                join {table} t on t.id = a.{table}_id) as x
            where data_object.id = x.id
        """
        )


def downgrade():
    op.drop_column("data_object", "workflow_type")
