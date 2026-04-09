"""add_fts_gin_indexes

Revision ID: b7d4b19db410
Revises: 87821b18f9e3
Create Date: 2026-04-08 15:51:00.970401

"""

from typing import Optional

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7d4b19db410"
down_revision: Optional[str] = "87821b18f9e3"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


# Note: The following is a comment from the original author of these SQL function definitions:
#       > Full-text search helper functions
#       >
#       > These SQL wrapper functions are IMMUTABLE (output depends solely on inputs),
#       > which enables functional GIN indexes on the study and biosample tables.
#
# Note: The `--sql`/`--end-sql` SQL comments are tokens that some code editor plugins look for in
#       order to know where to apply SQL syntax highlighting within literal strings. An example of
#       such a code editor plugin is:
#       https://marketplace.visualstudio.com/items?itemName=ptweir.python-string-sql
#
STUDY_FTS_FUNCTION_DDL = """--sql
    CREATE OR REPLACE FUNCTION nmdc_study_fts(
        p_id text,
        p_name text,
        p_description text,
        p_gold_name text,
        p_gold_description text,
        p_scientific_objective text,
        p_annotations jsonb
    ) RETURNS tsvector LANGUAGE sql IMMUTABLE PARALLEL SAFE
    AS $$
        SELECT to_tsvector(
            'simple',
            concat_ws(
                ' ',
                p_id,
                p_name,
                p_description,
                p_gold_name,
                p_gold_description,
                p_scientific_objective
            )
        ) || to_tsvector('simple', p_annotations)
    $$
--end-sql"""

BIOSAMPLE_FTS_FUNCTION_DDL = """--sql
    CREATE OR REPLACE FUNCTION nmdc_biosample_fts(
        p_id text,
        p_name text,
        p_description text,
        p_study_id text,
        p_env_broad_scale_id text,
        p_env_local_scale_id text,
        p_env_medium_id text,
        p_ecosystem text,
        p_ecosystem_category text,
        p_ecosystem_type text,
        p_ecosystem_subtype text,
        p_specific_ecosystem text,
        p_annotations jsonb
    ) RETURNS tsvector LANGUAGE sql IMMUTABLE PARALLEL SAFE
    AS $$
        SELECT to_tsvector(
            'simple',
            concat_ws(
                ' ',
                p_id,
                p_name,
                p_description,
                p_study_id,
                p_env_broad_scale_id,
                p_env_local_scale_id,
                p_env_medium_id,
                p_ecosystem,
                p_ecosystem_category,
                p_ecosystem_type,
                p_ecosystem_subtype,
                p_specific_ecosystem
            )
        ) || to_tsvector('simple', p_annotations)
    $$
--end-sql"""


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
    --end-sql""")
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
    --end-sql""")


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_biosample_fts")
    op.execute("DROP INDEX IF EXISTS ix_study_fts")
    op.execute("DROP FUNCTION IF EXISTS nmdc_biosample_fts")
    op.execute("DROP FUNCTION IF EXISTS nmdc_study_fts")
