"""metabolomics analysis

Revision ID: 5aa75e4c1cad
Revises: b267ff7d3c10
Create Date: 2021-01-29 14:24:23.486274

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5aa75e4c1cad"
down_revision: Optional[str] = "b267ff7d3c10"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.create_table(
        "metabolomics_analysis",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("git_url", sa.String(), nullable=False),
        sa.Column("started_at_time", sa.DateTime(), nullable=False),
        sa.Column("ended_at_time", sa.DateTime(), nullable=False),
        sa.Column("execution_resource", sa.String(), nullable=False),
        sa.Column("used", sa.String(), nullable=False),
        sa.Column("has_calibration", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["project.id"], name=op.f("fk_metabolomics_analysis_project_id_project")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_metabolomics_analysis")),
    )
    op.create_table(
        "metabolomics_analysis_input_association",
        sa.Column("metabolomics_analysis_id", sa.String(), nullable=True),
        sa.Column("data_object_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["data_object_id"],
            ["data_object.id"],
            name=op.f("fk_metabolomics_analysis_input_association_data_object_id_data_object"),
        ),
        sa.ForeignKeyConstraint(
            ["metabolomics_analysis_id"],
            ["metabolomics_analysis.id"],
            name=op.f(
                "fk_metabolomics_analysis_input_association_"
                "metabolomics_analysis_id_metabolomics_analysis"
            ),
        ),
        sa.UniqueConstraint(
            "metabolomics_analysis_id",
            "data_object_id",
            name=op.f("uq_metabolomics_analysis_input_association_metabolomics_analysis_id"),
        ),
    )
    op.create_table(
        "metabolomics_analysis_output_association",
        sa.Column("metabolomics_analysis_id", sa.String(), nullable=True),
        sa.Column("data_object_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["data_object_id"],
            ["data_object.id"],
            name=op.f("fk_metabolomics_analysis_output_association_data_object_id_data_object"),
        ),
        sa.ForeignKeyConstraint(
            ["metabolomics_analysis_id"],
            ["metabolomics_analysis.id"],
            name=op.f(
                "fk_metabolomics_analysis_output_association_"
                "metabolomics_analysis_id_metabolomics_analysis"
            ),
        ),
        sa.UniqueConstraint(
            "metabolomics_analysis_id",
            "data_object_id",
            name=op.f("uq_metabolomics_analysis_output_association_metabolomics_analysis_id"),
        ),
    )


def downgrade():
    op.drop_table("metabolomics_analysis_output_association")
    op.drop_table("metabolomics_analysis_input_association")
    op.drop_table("metabolomics_analysis")
