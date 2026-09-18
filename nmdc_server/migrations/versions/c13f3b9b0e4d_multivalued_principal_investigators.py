"""Make Study principal investigators multivalued.

Revision ID: c13f3b9b0e4d
Revises: 514cc831aa3b
Create Date: 2026-09-18

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c13f3b9b0e4d"
down_revision: Optional[str] = "514cc831aa3b"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.create_table(
        "study_principal_investigator_association",
        sa.Column("study_id", sa.String(), nullable=False),
        sa.Column("principal_investigator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["principal_investigator_id"],
            ["principal_investigator.id"],
            name=op.f(
                "fk_study_principal_investigator_association_principal_investigator_id_principal_investigator"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["study.id"],
            name=op.f("fk_study_principal_investigator_association_study_id_study"),
        ),
        sa.PrimaryKeyConstraint(
            "study_id",
            "principal_investigator_id",
            name=op.f("pk_study_principal_investigator_association"),
        ),
    )
    op.execute("""
        INSERT INTO study_principal_investigator_association (
            study_id,
            principal_investigator_id
        )
        SELECT id, principal_investigator_id
        FROM study
        WHERE principal_investigator_id IS NOT NULL
        """)
    op.drop_constraint(
        op.f("fk_study_principal_investigator_id_principal_investigator"),
        "study",
        type_="foreignkey",
    )
    op.drop_column("study", "principal_investigator_id")


def downgrade():
    op.add_column(
        "study",
        sa.Column(
            "principal_investigator_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        op.f("fk_study_principal_investigator_id_principal_investigator"),
        "study",
        "principal_investigator",
        ["principal_investigator_id"],
        ["id"],
    )
    op.execute("""
        UPDATE study
        SET principal_investigator_id = selected.principal_investigator_id
        FROM (
            SELECT DISTINCT ON (study_id) study_id, principal_investigator_id
            FROM study_principal_investigator_association
            ORDER BY study_id, principal_investigator_id
        ) AS selected
        WHERE study.id = selected.study_id
        """)
    op.drop_table("study_principal_investigator_association")
