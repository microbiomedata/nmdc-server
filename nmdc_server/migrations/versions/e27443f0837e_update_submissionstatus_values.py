"""empty message

Revision ID: e27443f0837e
Revises: ffa58e5f59fe
Create Date: 2025-07-18 19:36:11.484730

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op
from nmdc_schema.nmdc import SubmissionStatusEnum
from sqlalchemy.sql import column, table

# revision identifiers, used by Alembic.
revision: str = "e27443f0837e"
down_revision: Optional[str] = "ffa58e5f59fe"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None

STATUS_MAP = [
    {
        "old": "in-progress",
        "new": SubmissionStatusEnum.InProgress.text,
    },
    {
        "old": "Submitted- Pending Review",
        "new": SubmissionStatusEnum.SubmittedPendingReview.text,
    },
    {
        "old": "Complete",
        "new": SubmissionStatusEnum.Released.text,
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
