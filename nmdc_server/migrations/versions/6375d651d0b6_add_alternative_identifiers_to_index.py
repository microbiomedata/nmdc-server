"""Add alternate_identifiers to biosample FTS index

Revision ID: 6375d651d0b6
Revises: 34a0480316fa
Create Date: 2026-04-16 22:40:11.927656

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6375d651d0b6'
down_revision: Optional[str] = '34a0480316fa'
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.drop_index('ix_biosample_fts', table_name='biosample')
    op.create_index('ix_biosample_fts', 'biosample', [sa.text('nmdc_biosample_fts(id, name, description, study_id, env_broad_scale_id, env_local_scale_id, env_medium_id, ecosystem, ecosystem_category, ecosystem_type, ecosystem_subtype, specific_ecosystem, annotations, alternate_identifiers)')], unique=False, postgresql_using='gin')


def downgrade():
    op.drop_index('ix_biosample_fts', table_name='biosample')
    op.create_index('ix_biosample_fts', 'biosample', [sa.text('nmdc_biosample_fts(id::text, name::text, description::text, study_id::text, env_broad_scale_id::text, env_local_scale_id::text, env_medium_id::text, ecosystem::text, ecosystem_category::text, ecosystem_type::text, ecosystem_subtype::text, specific_ecosystem::text, annotations)')], unique=False, postgresql_using='gin')