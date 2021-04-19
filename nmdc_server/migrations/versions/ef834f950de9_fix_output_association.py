"""fix output_association

Revision ID: ef834f950de9
Revises: 430126297535
Create Date: 2021-04-19 17:11:42.931702

"""
from typing import Optional

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "ef834f950de9"
down_revision: Optional[str] = "430126297535"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.alter_column(
        "omics_processing_output_association", "project_id", new_column_name="omics_processing_id"
    )


def downgrade():
    pass
