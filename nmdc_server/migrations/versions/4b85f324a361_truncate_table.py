"""truncate table

Revision ID: 4b85f324a361
Revises: 9da3cb811a0e
Create Date: 2021-01-25 14:16:53.096986

"""
from typing import Optional

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "4b85f324a361"
down_revision: Optional[str] = "9da3cb811a0e"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.execute(
        """
CREATE OR REPLACE FUNCTION truncate_tables() RETURNS void AS $$
DECLARE
    statements CURSOR FOR
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public' and tablename <> 'alembic_version';
BEGIN
    FOR stmt IN statements LOOP
        EXECUTE 'TRUNCATE TABLE ' || quote_ident(stmt.tablename) || ' CASCADE;';
    END LOOP;
END;
$$ LANGUAGE plpgsql;
    """
    )


def downgrade():
    pass
