import threading
from datetime import datetime, timedelta, timezone

from github import Auth, Github, GithubIntegration
from github.GithubObject import NotSet
from github.Issue import Issue
from github.Repository import Repository

from nmdc_server.config import settings

# Refresh the token when it has fewer than this many minutes remaining, so that we don't attempt to
# use a token that may expire mid-request.
_REFRESH_BUFFER = timedelta(minutes=5)

_lock = threading.Lock()
_cached_token: str = ""
_token_expires_at: datetime | None = None
_private_key: str | None = None

if settings.github_submission_bot_private_key_file is not None:
    try:
        with open(settings.github_submission_bot_private_key_file) as f:
            _private_key = f.read()
    except OSError:
        # If the file can't be read, we leave _private_key as None and let the error be raised
        # later when we try to get a token.
        pass


class MissingCredentialsError(Exception):
    """Raised when GitHub credentials are missing or incomplete."""


def _get_installation_token() -> str:
    """Return a cached installation token, refreshing it only when needed."""
    global _cached_token, _token_expires_at

    now = datetime.now(timezone.utc)

    # Fast path: token is still valid (check without acquiring the lock)
    if _cached_token and _token_expires_at and now < _token_expires_at - _REFRESH_BUFFER:
        return _cached_token

    # Slow path: refresh the token under a lock so concurrent requests
    # don't all try to refresh at the same time.
    with _lock:
        # Re-check after acquiring the lock — another thread may have refreshed.
        if _cached_token and _token_expires_at and now < _token_expires_at - _REFRESH_BUFFER:
            return _cached_token

        if settings.github_submission_bot_app_id is None or _private_key is None:
            raise MissingCredentialsError("NMDC Submission Bot credentials not set")

        auth = Auth.AppAuth(settings.github_submission_bot_app_id, _private_key)
        integration = GithubIntegration(auth=auth)
        org, repo = settings.github_issues_repo.split("/", maxsplit=1)
        installation = integration.get_repo_installation(org, repo)
        installation_auth = integration.get_access_token(installation.id)

        _cached_token = installation_auth.token
        # PyGithub returns expires_at as a datetime object
        _token_expires_at = installation_auth.expires_at.replace(tzinfo=timezone.utc)

        return _cached_token


def _get_issues_repo() -> Repository:
    """Return the GitHub repository object for the configured issues repository."""
    client = get_client()
    return client.get_repo(settings.github_issues_repo)


def get_client() -> Github:
    """Return an authenticated GitHub client using a cached installation token."""
    return Github(auth=Auth.Token(_get_installation_token()))


def create_issue(title: str, body: str, assignee: str | None = None) -> str:
    """Create a GitHub issue in the configured repository and return the issue number as a string."""
    repo = _get_issues_repo()
    issue = repo.create_issue(title=title, body=body, assignee=assignee or NotSet)
    return str(issue.number)


def get_issue(issue_number: str) -> Issue:
    """Get a GitHub issue by its number."""
    repo = _get_issues_repo()
    return repo.get_issue(int(issue_number))


def add_issue_comment(issue: str | Issue, comment: str) -> None:
    """Add a comment to an existing GitHub issue."""
    issue_obj = issue if isinstance(issue, Issue) else get_issue(issue)
    issue_obj.create_comment(comment)


def reopen_issue(issue: str | Issue) -> None:
    """Reopen a closed GitHub issue.

    If the issue is not closed, this is a no-op.
    """
    issue_obj = issue if isinstance(issue, Issue) else get_issue(issue)
    if issue_obj.state == "closed":
        issue_obj.edit(state="open", state_reason="reopened")
