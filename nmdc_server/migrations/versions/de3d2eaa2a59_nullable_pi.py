"""Make principal investigator nullable

Revision ID: de3d2eaa2a59
Revises: 1de891717fc0
Create Date: 2023-10-06 19:32:42.311755

"""

from typing import Optional

from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "de3d2eaa2a59"
down_revision: Optional[str] = "1de891717fc0"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "study", "principal_investigator_id", existing_type=postgresql.UUID(), nullable=True
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "study", "principal_investigator_id", existing_type=postgresql.UUID(), nullable=False
    )
    # ### end Alembic commands ###
