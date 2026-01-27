"""Add github issue for existing submissions

Revision ID: c5852f4f16b1
Revises: 23ef8096759e
Create Date: 2025-12-24 00:00:40.880570

"""

import csv
from typing import Optional

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c5852f4f16b1"
down_revision: Optional[str] = "23ef8096759e"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None

# GH issues for submissions (found via SamO local file scripts/find_submission_github_issues.py)
with open(
    "nmdc_server/migrations/versions/submission_github_issues_20260121.csv",
    "r",
    newline="",
    encoding="utf-8",
) as csvfile:
    csv_reader = csv.DictReader(csvfile)
    rows = list(csv_reader)  # Read all rows once
    gh_matches = {
        row["Submission ID"]: row["GitHub Issue"] for row in rows if row["GitHub Issue"] != "N/A"
    }
    gh_no_match_confirmed = {
        row["Submission ID"] for row in rows if row["Notes"] == "No Issue (Confirmed OK)"
    }


def upgrade():  # noqa: C901

    # Get database connection
    connection = op.get_bind()

    # Add new column for GitHub issue
    op.add_column("submission_metadata", sa.Column("submission_issue", sa.String(), nullable=True))

    # Add GH issues for existing submissions
    for submission_id, issue_number in gh_matches.items():
        connection.execute(
            sa.text(
                "UPDATE submission_metadata SET submission_issue = :issue_number WHERE id = :id"
            ),
            {"issue_number": str(issue_number), "id": submission_id},
        )

    # Report any submissions that should have a GH issue but don't (created after 2023, not InProgress)
    result = connection.execute(
        sa.text("""
            SELECT id, status
            FROM submission_metadata
            WHERE (submission_issue is NULL AND created >= '2024-01-01' AND status != 'InProgress' AND id NOT IN :no_match_confirmed)
            """),
        {"no_match_confirmed": tuple(gh_no_match_confirmed)},
    )
    missing_gh_issue = result.fetchall()

    if missing_gh_issue:
        print(
            "WARNING! The following submissions are missing a Github issue when they should have one. "
            "Likely submission occurred after migrator was created."
            "Please manually search and update `submission_issue` in the database accordingly:"
        )
        for issue in missing_gh_issue:
            print(f"Submission: {issue[0]}, Status: {issue[1]}")


def downgrade():
    op.drop_column("submission_metadata", "submission_issue")
