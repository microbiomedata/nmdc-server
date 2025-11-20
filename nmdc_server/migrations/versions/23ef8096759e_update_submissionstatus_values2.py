"""Make submission status consistent with enum updates

Revision ID: 23ef8096759e
Revises: 9a0ff33a4e6b
Create Date: 2025-11-17 18:41:13.169730

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op
from nmdc_schema.nmdc import SubmissionStatusEnum
from sqlalchemy.sql import column, table

# revision identifiers, used by Alembic.
revision: str = "23ef8096759e"
down_revision: Optional[str] = "9a0ff33a4e6b"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None

STATUS_MAP = [
    {
        "old": "ResubmittedPendingReview",
        "new": SubmissionStatusEnum.SubmittedPendingReview.text,
    },
    {
        "old": "InProgressUpdate",
        "new": SubmissionStatusEnum.InProgress.text,
    },
    {
        "old": "PendingUserFacility",
        "new": SubmissionStatusEnum.ApprovedPendingUserFacility.text,
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
