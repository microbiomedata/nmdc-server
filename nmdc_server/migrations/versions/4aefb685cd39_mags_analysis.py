"""mags analysis

Revision ID: 4aefb685cd39
Revises: e2df18f14429
Create Date: 2021-01-29 10:45:14.520583

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "4aefb685cd39"
down_revision: Optional[str] = "e2df18f14429"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.create_table(
        "mags_analysis",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("git_url", sa.String(), nullable=False),
        sa.Column("started_at_time", sa.DateTime(), nullable=False),
        sa.Column("ended_at_time", sa.DateTime(), nullable=False),
        sa.Column("execution_resource", sa.String(), nullable=False),
        sa.Column("input_contig_num", sa.BigInteger(), nullable=False),
        sa.Column("too_short_contig_num", sa.BigInteger(), nullable=False),
        sa.Column("lowDepth_contig_num", sa.BigInteger(), nullable=False),
        sa.Column("unbinned_contig_num", sa.BigInteger(), nullable=False),
        sa.Column("binned_contig_num", sa.BigInteger(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["project.id"], name=op.f("fk_mags_analysis_project_id_project")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_mags_analysis")),
    )
    op.create_table(
        "mag",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mags_analysis_id", sa.String(), nullable=False),
        sa.Column("bin_name", sa.String(), nullable=False),
        sa.Column("number_of_contig", sa.BigInteger(), nullable=False),
        sa.Column("completeness", sa.Float(), nullable=False),
        sa.Column("contamination", sa.Float(), nullable=False),
        sa.Column("gene_count", sa.BigInteger(), nullable=False),
        sa.Column("bin_quality", sa.String(), nullable=False),
        sa.Column("num_16s", sa.BigInteger(), nullable=False),
        sa.Column("num_5s", sa.BigInteger(), nullable=False),
        sa.Column("num_23s", sa.BigInteger(), nullable=False),
        sa.Column("num_tRNA", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["mags_analysis_id"],
            ["mags_analysis.id"],
            name=op.f("fk_mag_mags_analysis_id_mags_analysis"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_mag")),
    )
    op.create_table(
        "mags_analysis_input_association",
        sa.Column("mags_analysis_id", sa.String(), nullable=True),
        sa.Column("data_object_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["data_object_id"],
            ["data_object.id"],
            name=op.f("fk_mags_analysis_input_association_data_object_id_data_object"),
        ),
        sa.ForeignKeyConstraint(
            ["mags_analysis_id"],
            ["mags_analysis.id"],
            name=op.f("fk_mags_analysis_input_association_mags_analysis_id_mags_analysis"),
        ),
        sa.UniqueConstraint(
            "mags_analysis_id",
            "data_object_id",
            name=op.f("uq_mags_analysis_input_association_mags_analysis_id"),
        ),
    )
    op.create_table(
        "mags_analysis_output_association",
        sa.Column("mags_analysis_id", sa.String(), nullable=True),
        sa.Column("data_object_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["data_object_id"],
            ["data_object.id"],
            name=op.f("fk_mags_analysis_output_association_data_object_id_data_object"),
        ),
        sa.ForeignKeyConstraint(
            ["mags_analysis_id"],
            ["mags_analysis.id"],
            name=op.f("fk_mags_analysis_output_association_mags_analysis_id_mags_analysis"),
        ),
        sa.UniqueConstraint(
            "mags_analysis_id",
            "data_object_id",
            name=op.f("uq_mags_analysis_output_association_mags_analysis_id"),
        ),
    )


def downgrade():
    op.drop_table("mags_analysis_output_association")
    op.drop_table("mags_analysis_input_association")
    op.drop_table("mag")
    op.drop_table("mags_analysis")
