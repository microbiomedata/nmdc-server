"""add submission_sample_set.github_issue column

This migration adds a new nullable string column named `github_issue` to the `submission_sample_set`
table. It also renames the existing `submission_issue` column in the `submission_metadata` table to
`github_issue` for consistency.

Revision ID: f7ab5b690b5e
Revises: 2d175e58c0ae
Create Date: 2026-06-02 18:03:27.546485

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f7ab5b690b5e"
down_revision: Optional[str] = "2d175e58c0ae"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # Add the new `github_issue` column to the `submission_sample_set` table
    op.add_column("submission_sample_set", sa.Column("github_issue", sa.String(), nullable=True))

    # Add the new `github_issue` column to the `submission_metadata` table and copy existing data
    # from the old `submission_issue` column, then drop the old `submission_issue` column
    op.add_column("submission_metadata", sa.Column("github_issue", sa.String(), nullable=True))
    op.execute("""
        UPDATE submission_metadata
        SET github_issue = submission_issue
    """)
    op.drop_column("submission_metadata", "submission_issue")


def downgrade():
    # Add the old `submission_issue` column back to the `submission_metadata` table, copy data from
    # the `github_issue` column, then drop the `github_issue` column
    op.add_column(
        "submission_metadata",
        sa.Column("submission_issue", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.execute("""
        UPDATE submission_metadata
        SET submission_issue = github_issue
    """)
    op.drop_column("submission_metadata", "github_issue")
    op.drop_column("submission_sample_set", "github_issue")
