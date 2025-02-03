"""

Adds date_last_modified to MetadataSubmission

Revision ID: 6e6dec0daa7c
Revises: 18127fd43a8b
Create Date: 2025-02-03 18:58:55.592754

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e6dec0daa7c'
down_revision: Optional[str] = '18127fd43a8b'
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('submission_metadata', sa.Column('date_last_modified', sa.DateTime(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('submission_metadata', 'date_last_modified')
    # ### end Alembic commands ###
