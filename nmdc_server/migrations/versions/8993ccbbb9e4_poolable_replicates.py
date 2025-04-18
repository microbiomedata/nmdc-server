"""Track data_generations associated via manifest of type
poolable_replicates

Revision ID: 8993ccbbb9e4
Revises: cf73ba2f0f85
Create Date: 2025-03-26 16:45:50.793640

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8993ccbbb9e4"
down_revision: Optional[str] = "cf73ba2f0f85"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "omics_processing", sa.Column("poolable_replicates_manifest_id", sa.String(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("omics_processing", "poolable_replicates_manifest_id")
    # ### end Alembic commands ###
