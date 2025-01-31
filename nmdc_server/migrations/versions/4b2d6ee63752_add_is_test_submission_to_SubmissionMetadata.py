""" Migrator for is_test_submission on SubmissionMetadata
This field added as a change to enable the differentiation between test submissions
(those done in training/at a conference demo) and real submissions

Revision ID: 4b2d6ee63752
Revises: afa1ff687968
Create Date: 2025-01-03 18:07:09.029643

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4b2d6ee63752"
down_revision: Optional[str] = "afa1ff687968"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.add_column(
        "submission_metadata",
        sa.Column(
            "is_test_submission", sa.Boolean(), nullable=False, server_default=sa.sql.False_()
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    op.drop_column("submission_metadata", "is_test_submission")
    # ### end Alembic commands ###
