"""empty message

Revision ID: c5852f4f16b1
Revises: 23ef8096759e
Create Date: 2025-12-24 00:00:40.880570

"""
from typing import Optional
import time

from alembic import op
import sqlalchemy as sa
import requests
from uuid import UUID
import csv

from nmdc_server.config import settings

# revision identifiers, used by Alembic.
revision: str = 'c5852f4f16b1'
down_revision: Optional[str] = '23ef8096759e'
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def search_github_issues_batch(submission_ids: list, headers: dict):
    """
    Search for multiple submission IDs in a single API call using OR operators.
    Returns a dict mapping submission_id -> list of matching issues.
    """
    search_url = "https://api.github.com/search/issues"
    
    # Build query with OR operators for all submission IDs
    id_queries = ' OR '.join([f'"{str(sid)}"' for sid in submission_ids])
    query = f'({id_queries}) repo:microbiomedata/issues is:issue'
    
    params = {
        "q": query,
        "per_page": 100
    }
    
    try:
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        issues = data.get('items', [])
        
        # Map each submission ID to its matching issues
        results = {str(sid): [] for sid in submission_ids}
        
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


def upgrade():
    op.add_column('submission_metadata', sa.Column('submission_issue', sa.String(), nullable=True))
    
    # Get GitHub configuration from settings
    github_token = settings.github_authentication_token
    if not github_token:
        print("WARNING: GitHub settings not configured. Skipping GitHub issue population.")
        return
    
    # Set up GitHub API headers
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Get database connection
    connection = op.get_bind()
    
    result = connection.execute(sa.text(
        "SELECT id, status FROM submission_metadata WHERE submission_issue is NULL"
    ))
    submissions = result.fetchall()
    
    print(f"Found {len(submissions)} submissions to process")
    
    manuel_review = []
    
    # Process submissions in batches to reduce API calls
    batch_size = 5  # Process 5 submissions per API call (GitHub has query length limits)
    total_batches = (len(submissions) + batch_size - 1) // batch_size
    
    for batch_num in range(0, len(submissions), batch_size):
        batch = submissions[batch_num:batch_num + batch_size]
        batch_submission_ids = [row[0] for row in batch]
        
        print(f"Batch {batch_num // batch_size + 1}/{total_batches}: Searching {len(batch)} submissions...")
        
        # Search for all submission IDs in this batch with a single API call
        issues_by_id = search_github_issues_batch(batch_submission_ids, headers)
        
        # Process each submission in the batch
        for row in batch:
            submission_id = row[0]
            submission_status = row[1]
            issues = issues_by_id.get(str(submission_id), [])
        
        if issues:

            # Multiple issues found, check issue states
            if len(issues) > 1:
                states = [issue.get('state') for issue in issues]

                # If only one is open, update database
                if states.count('open') == 1:
                    for issue in issues:
                        if issue.get('state') == 'open':
                            issue_number = issue.get('number')
                            connection.execute(
                                sa.text("UPDATE submission_metadata SET submission_issue = :issue_number WHERE id = :id"),
                                {"issue_number": str(issue_number), "id": submission_id}
                            )
                            break

                # If no open issues or more than one, log all for manual review
                else:
                    for issue in issues:
                        manuel_review.append([submission_id, submission_status, issue.get('number'), issue.get('state')])

            # Single issue found, update database
            else:
                issue_number = issues[0].get('number')
                if issue_number:
                    connection.execute(
                        sa.text("UPDATE submission_metadata SET submission_issue = :issue_number WHERE id = :id"),
                        {"issue_number": str(issue_number), "id": submission_id}
                    )

        # No issues found even though submission isn't `InProgress`, log for manual review
        else:
            if submission_status != 'InProgress':
                manuel_review.append([submission_id, submission_status, 'None Found', 'N/A'])
        
        # Add delay between batches to avoid rate limiting (2 seconds per batch)
        if batch_num + batch_size < len(submissions):
            time.sleep(2)
    
    print(f"\nProcessing complete!")
    if manuel_review:
        for issue in manuel_review:
            print(f"Submission: {issue[0]}, Status: {issue[1]}, GH Issue: {issue[2]}, GH Issue State: {issue[3]}")


def downgrade():
    op.drop_column('submission_metadata', 'submission_issue')
