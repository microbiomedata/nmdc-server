"""empty message

Revision ID: c5852f4f16b1
Revises: 23ef8096759e
Create Date: 2025-12-24 00:00:40.880570

"""

import time
from datetime import datetime
from typing import Optional

import requests
import sqlalchemy as sa
from alembic import op

from nmdc_server.config import settings

# revision identifiers, used by Alembic.
revision: str = "c5852f4f16b1"
down_revision: Optional[str] = "23ef8096759e"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def search_github_issues_batch(submission_ids: list, headers: dict):
    """
    Search for multiple submission IDs in a single API call using OR operators.
    Returns a dict mapping submission_id -> list of matching issues.
    """
    search_url = "https://api.github.com/search/issues"

    # Build query with OR operators for all submission IDs
    id_queries = " OR ".join([f'"{str(sid)}"' for sid in submission_ids])
    query = f"({id_queries}) repo:microbiomedata/issues is:issue"

    params = {"q": query, "per_page": "100"}

    try:
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        issues = data.get("items", [])

        # Map each submission ID to its matching issues
        results: dict[str, list] = {str(sid): [] for sid in submission_ids}

        for issue in issues:
            title = issue.get("title", "") or ""
            body = issue.get("body", "") or ""

            if "NMDC Submission" in title:
                # Check which submission ID(s) this issue matches
                for sid in submission_ids:
                    sid_str = str(sid)
                    if sid_str in title or sid_str in body:
                        results[sid_str].append(issue)

        return results

    except requests.RequestException as e:
        print(f"Request failed to check existing GitHub issues: {str(e)}")
        return {str(sid): [] for sid in submission_ids}


# Manually reviewed Github issues
manual_gh_issue_entries = {
    "adc54fc8-2c94-457d-9b5c-89d7f005fb59": "999",
    "a2cba002-2b81-446c-959b-4b933b3424ef": "1400",
    "81041da9-3b7a-40c9-a66b-5166ccb3367e": "667",
    "7ab5c37b-d429-4f31-8970-8e766336921b": "1128",
    "e66b72e9-1e0d-4f0c-910d-97ec461e0c2b": "1508",
    "df1d2ba5-33be-43d0-b4b9-e5d57ace3f70": "1100",
    "e3b3be26-7da9-417d-b3a6-4fc747a1d586": "921",
    "1eced560-5f6b-436f-9ccc-4fca9ad2ed48": "1099",
    "3ebdb329-42ad-427f-bf25-7dc74fc4cc72": "1101",
    "1efa01f4-2298-4ecb-99af-6e03d8898534": "1357",
    "b23188f2-8c1c-44b8-b2f8-9548c564282d": "1366",
    "77965dc2-6d0a-48e3-8e48-e804d442d967": "1439",
}


def upgrade():  # noqa: C901

    # Get database connection
    connection = op.get_bind()

    # Add new column for GitHub issue
    op.add_column("submission_metadata", sa.Column("submission_issue", sa.String(), nullable=True))

    # Pre-fill manually reviewed GitHub issues
    for submission_id, issue_number in manual_gh_issue_entries.items():
        connection.execute(
            sa.text(
                "UPDATE submission_metadata SET submission_issue = :issue_number WHERE id = :id"
            ),
            {"issue_number": str(issue_number), "id": submission_id},
        )

    # Get GitHub configuration from settings
    github_token = settings.github_authentication_token
    if not github_token:
        print("WARNING: GitHub settings not configured. Skipping GitHub issue population.")
        return

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Query submissions without a GitHub issue
    result = connection.execute(
        sa.text(
            "SELECT id, status, created FROM submission_metadata WHERE submission_issue is NULL"
        )
    )
    submissions = result.fetchall()

    print(f"Found {len(submissions)} submissions to process")

    manual_review = []

    # Query submissions in batches to reduce API calls
    batch_size = 5  # Process 5 submissions per API call (GitHub has query length limits)
    total_batches = (len(submissions) + batch_size - 1) // batch_size

    for batch_num in range(0, len(submissions), batch_size):
        batch_submissions = submissions[batch_num : batch_num + batch_size]
        batch_submission_ids = [row[0] for row in batch_submissions]

        print(
            f"Batch {batch_num // batch_size + 1}/{total_batches}: Searching {len(batch_submissions)} submissions..."
        )

        gh_issues_by_id = search_github_issues_batch(batch_submission_ids, headers)

        print(
            f"Found issues for {sum(len(v) for v in gh_issues_by_id.values())} submissions in this batch."
        )

        # Process GH issues for each submission in the batch
        for row in batch_submissions:
            submission_id = row[0]
            submission_status = row[1]
            submission_created = row[2]
            issues = gh_issues_by_id.get(str(submission_id), [])

            if issues:

                # Multiple GH issues found, log for manual review
                if len(issues) > 1:
                    for issue in issues:
                        manual_review.append(
                            [
                                submission_id,
                                submission_status,
                                issue.get("number"),
                                issue.get("state"),
                                submission_created,
                            ]
                        )

                # Single GH issue found, update database
                else:
                    issue_number = issues[0].get("number")
                    if issue_number:
                        connection.execute(
                            sa.text(
                                "UPDATE submission_metadata SET submission_issue = :issue_number WHERE id = :id"
                            ),
                            {"issue_number": str(issue_number), "id": submission_id},
                        )

            # No GH issues but its status other than "InProgress" and submission created after 2023, log for manual review
            else:
                if (submission_status != "InProgress") & (
                    submission_created >= datetime(2024, 1, 1)
                ):
                    manual_review.append(
                        [
                            submission_id,
                            submission_status,
                            "None Found",
                            "N/A",
                            submission_created,
                        ]
                    )

        # Add delay between batches to avoid rate limiting (2 seconds per batch)
        if batch_num + batch_size < len(submissions):
            time.sleep(2)

    print("\nProcessing complete!")
    if manual_review:
        print(
            "Submissions that match multiple GH issues OR are missing a GH issue AND are not `InProgress` AND started after 2023. Manual review needed because single GH issue expected."
        )
        for issue in manual_review:
            print(
                f"Submission: {issue[0]}, Status: {issue[1]}, GH Issue: {issue[2]}, GH Issue State: {issue[3]}, Date Created: {issue[4]}"
            )


def downgrade():
    op.drop_column("submission_metadata", "submission_issue")
