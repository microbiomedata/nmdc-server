"""read based analysis

Revision ID: b267ff7d3c10
Revises: a60ed1c6fd15
Create Date: 2021-01-29 11:56:53.918642

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b267ff7d3c10"
down_revision: Optional[str] = "a60ed1c6fd15"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.create_table(
        "read_based_analysis",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("git_url", sa.String(), nullable=False),
        sa.Column("started_at_time", sa.DateTime(), nullable=False),
        sa.Column("ended_at_time", sa.DateTime(), nullable=False),
        sa.Column("execution_resource", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["project.id"], name=op.f("fk_read_based_analysis_project_id_project")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_read_based_analysis")),
    )
    op.create_table(
        "read_based_analysis_input_association",
        sa.Column("read_based_analysis_id", sa.String(), nullable=True),
        sa.Column("data_object_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["data_object_id"],
            ["data_object.id"],
            name=op.f("fk_read_based_analysis_input_association_data_object_id_data_object"),
        ),
        sa.ForeignKeyConstraint(
            ["read_based_analysis_id"],
            ["read_based_analysis.id"],
            name=op.f(
                "fk_read_based_analysis_input_association_"
                "read_based_analysis_id_read_based_analysis"
            ),
        ),
        sa.UniqueConstraint(
            "read_based_analysis_id",
            "data_object_id",
            name=op.f("uq_read_based_analysis_input_association_read_based_analysis_id"),
        ),
    )
    op.create_table(
        "read_based_analysis_output_association",
        sa.Column("read_based_analysis_id", sa.String(), nullable=True),
        sa.Column("data_object_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["data_object_id"],
            ["data_object.id"],
            name=op.f("fk_read_based_analysis_output_association_data_object_id_data_object"),
        ),
        sa.ForeignKeyConstraint(
            ["read_based_analysis_id"],
            ["read_based_analysis.id"],
            name=op.f(
                "fk_read_based_analysis_output_association_"
                "read_based_analysis_id_read_based_analysis"
            ),
        ),
        sa.UniqueConstraint(
            "read_based_analysis_id",
            "data_object_id",
            name=op.f("uq_read_based_analysis_output_association_read_based_analysis_id"),
        ),
    )


def downgrade():
    op.drop_table("read_based_analysis_output_association")
    op.drop_table("read_based_analysis_input_association")
    op.drop_table("read_based_analysis")
