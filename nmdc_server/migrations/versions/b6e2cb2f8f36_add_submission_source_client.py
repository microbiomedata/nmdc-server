"""Add source_client column to submission_metadata table

Revision ID: b6e2cb2f8f36
Revises: 6cdad9ad6543
Create Date: 2024-07-17 22:52:01.118381

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b6e2cb2f8f36"
down_revision: Optional[str] = "6cdad9ad6543"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # The enum type must be created manually first. For some reason add_column
    # doesn't do it automatically.
    submissionsourceclient_enum = sa.Enum(
        "submission_portal", "field_notes", name="submissionsourceclient"
    )
    submissionsourceclient_enum.create(op.get_bind())

    op.add_column(
        "submission_metadata",
        sa.Column(
            "source_client",
            submissionsourceclient_enum,
            nullable=True,
        ),
    )

    # Assume that all existing submissions were created by the submission portal
    op.execute("UPDATE submission_metadata SET source_client = 'submission_portal'")

    op.create_unique_constraint(
        op.f("uq_submission_role_submission_id"), "submission_role", ["submission_id", "user_orcid"]
    )


def downgrade():
    op.drop_constraint(op.f("uq_submission_role_submission_id"), "submission_role", type_="unique")
    op.drop_column("submission_metadata", "source_client")
    op.execute("DROP TYPE submissionsourceclient")
