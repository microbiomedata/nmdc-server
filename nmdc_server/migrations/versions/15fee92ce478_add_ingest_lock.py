"""add ingest lock

Revision ID: 15fee92ce478
Revises: 0464d245742c
Create Date: 2021-02-11 15:34:45.396912

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "15fee92ce478"
down_revision: Optional[str] = "0464d245742c"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.create_table(
        "ingest_lock",
        sa.Column("id", sa.Boolean(), nullable=False),
        sa.Column("started", sa.DateTime(), nullable=False),
        sa.CheckConstraint("id", name=op.f("ck_ingest_lock_singleton")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ingest_lock")),
    )
    op.execute(
        """
CREATE OR REPLACE FUNCTION truncate_tables() RETURNS void AS $$
DECLARE
    statements CURSOR FOR
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
            and tablename <> 'alembic_version'
            and tablename <> 'file_download'
            and tablename <> 'ingest_lock';
BEGIN
    FOR stmt IN statements LOOP
        EXECUTE 'TRUNCATE TABLE ' || quote_ident(stmt.tablename) || ' CASCADE;';
    END LOOP;
END;
$$ LANGUAGE plpgsql;
    """
    )


def downgrade():
    op.drop_table("ingest_lock")
