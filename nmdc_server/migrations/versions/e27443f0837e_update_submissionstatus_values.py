"""empty message

Revision ID: e27443f0837e
Revises: 6cb0b331ce8c
Create Date: 2025-07-18 19:36:11.484730

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import column, table

from nmdc_server.models import get_submission_status_enum

SubmissionStatusEnum = get_submission_status_enum()

# revision identifiers, used by Alembic.
revision: str = "e27443f0837e"
down_revision: Optional[str] = "6cb0b331ce8c"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


STATUS_MAP = [
    {
        "old": "in-progress",
        "new": SubmissionStatusEnum["InProgress"].title,
    },
    {
        "old": "Submitted- Pending Review",
        "new": SubmissionStatusEnum["SubmittedPendingReview"].title,
    },
    {
        "old": "Complete",
        "new": SubmissionStatusEnum["Released"].title,
    },
]


def upgrade():
    data_object = table("submission_metadata", column("status", sa.String))
    for mapping in STATUS_MAP:
        op.execute(
            data_object.update()
            .where(data_object.c.status == mapping["old"])
            .values(status=mapping["new"])
        )


def downgrade():
    data_object = table("submission_metadata", column("status", sa.String))
    for mapping in STATUS_MAP:
        op.execute(
            data_object.update()
            .where(data_object.c.status == mapping["new"])
            .values(status=mapping["old"])
        )
