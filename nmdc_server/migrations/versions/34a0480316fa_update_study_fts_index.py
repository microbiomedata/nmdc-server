"""Add columns to study FTS index

Revision ID: 34a0480316fa
Revises: b7d4b19db410
Create Date: 2026-04-15 17:37:07.318677

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "34a0480316fa"
down_revision: Optional[str] = "b7d4b19db410"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.drop_index("ix_study_fts", table_name="study", postgresql_using="gin")
    op.create_index(
        "ix_study_fts",
        "study",
        [
            sa.text(
                "nmdc_study_fts(id, name, description, gold_name, gold_description, scientific_objective, annotations, part_of, children)"
            )
        ],
        unique=False,
        postgresql_using="gin",
    )


def downgrade():
    op.drop_index("ix_study_fts", table_name="study", postgresql_using="gin")
    op.create_index(
        "ix_study_fts",
        "study",
        [
            sa.text(
                "nmdc_study_fts(id::text, name::text, description::text, gold_name::text, gold_description::text, scientific_objective::text, annotations)"
            )
        ],
        unique=False,
        postgresql_using="gin",
    )
