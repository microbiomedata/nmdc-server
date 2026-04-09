"""add_fts_gin_indexes

Revision ID: b7d4b19db410
Revises: 87821b18f9e3
Create Date: 2026-04-08 15:51:00.970401

"""

from typing import Optional

from alembic import op

# The function DDL lives in models.py next to the classes that use it.
from nmdc_server.models import BIOSAMPLE_FTS_FUNCTION_DDL, STUDY_FTS_FUNCTION_DDL

# revision identifiers, used by Alembic.
revision: str = "b7d4b19db410"
down_revision: Optional[str] = "87821b18f9e3"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.execute(BIOSAMPLE_FTS_FUNCTION_DDL)
    op.execute(STUDY_FTS_FUNCTION_DDL)
    op.execute("""--sql
        CREATE INDEX ix_biosample_fts ON biosample USING gin (
            nmdc_biosample_fts(
                id,
                name,
                description,
                study_id,
                env_broad_scale_id,
                env_local_scale_id,
                env_medium_id,
                ecosystem,
                ecosystem_category,
                ecosystem_type,
                ecosystem_subtype,
                specific_ecosystem,
                annotations
            )
        )
    """)
    op.execute("""--sql
        CREATE INDEX ix_study_fts ON study USING gin (
            nmdc_study_fts(
                id,
                name,
                description,
                gold_name,
                gold_description,
                scientific_objective,
                annotations
            )
        )
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_biosample_fts")
    op.execute("DROP INDEX IF EXISTS ix_study_fts")
    op.execute("DROP FUNCTION IF EXISTS nmdc_biosample_fts")
    op.execute("DROP FUNCTION IF EXISTS nmdc_study_fts")
