"""nom analysis

Revision ID: a60ed1c6fd15
Revises: 4aefb685cd39
Create Date: 2021-01-29 11:28:12.035062

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a60ed1c6fd15"
down_revision: Optional[str] = "4aefb685cd39"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.create_table(
        "nom_analysis",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("git_url", sa.String(), nullable=False),
        sa.Column("started_at_time", sa.DateTime(), nullable=False),
        sa.Column("ended_at_time", sa.DateTime(), nullable=False),
        sa.Column("execution_resource", sa.String(), nullable=False),
        sa.Column("used", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["project.id"], name=op.f("fk_nom_analysis_project_id_project")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_nom_analysis")),
    )
    op.create_table(
        "nom_analysis_input_association",
        sa.Column("nom_analysis_id", sa.String(), nullable=True),
        sa.Column("data_object_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["data_object_id"],
            ["data_object.id"],
            name=op.f("fk_nom_analysis_input_association_data_object_id_data_object"),
        ),
        sa.ForeignKeyConstraint(
            ["nom_analysis_id"],
            ["nom_analysis.id"],
            name=op.f("fk_nom_analysis_input_association_nom_analysis_id_nom_analysis"),
        ),
        sa.UniqueConstraint(
            "nom_analysis_id",
            "data_object_id",
            name=op.f("uq_nom_analysis_input_association_nom_analysis_id"),
        ),
    )
    op.create_table(
        "nom_analysis_output_association",
        sa.Column("nom_analysis_id", sa.String(), nullable=True),
        sa.Column("data_object_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["data_object_id"],
            ["data_object.id"],
            name=op.f("fk_nom_analysis_output_association_data_object_id_data_object"),
        ),
        sa.ForeignKeyConstraint(
            ["nom_analysis_id"],
            ["nom_analysis.id"],
            name=op.f("fk_nom_analysis_output_association_nom_analysis_id_nom_analysis"),
        ),
        sa.UniqueConstraint(
            "nom_analysis_id",
            "data_object_id",
            name=op.f("uq_nom_analysis_output_association_nom_analysis_id"),
        ),
    )


def downgrade():
    op.drop_table("nom_analysis_output_association")
    op.drop_table("nom_analysis_input_association")
    op.drop_table("nom_analysis")
