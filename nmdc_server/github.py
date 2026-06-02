import threading
from datetime import datetime, timedelta, timezone

from github import Auth, Github, GithubIntegration
from github.GithubObject import NotSet
from github.Issue import Issue
from github.Repository import Repository

from nmdc_server import schemas_submission
from nmdc_server.config import settings
from nmdc_server.logger import get_logger
from nmdc_server.models import SubmissionMetadata, SubmissionSampleSet, User

logger = get_logger(__name__)

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


def create_issue(title: str, body: str, assignee: str | None = None) -> Issue:
    """Create a GitHub issue in the configured repository and return the Issue object."""
    repo = _get_issues_repo()
    return repo.create_issue(title=title, body=body, assignee=assignee or NotSet)


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


def _format_body_list(
    fields: tuple[tuple[str, str], ...], optional_fields: tuple[tuple[str, str | None], ...]
) -> str:
    """Format a list of (name, value) pairs into a GitHub issue body."""
    all_fields = list(fields)
    for field_name, field_value in optional_fields:
        if field_value:
            all_fields.append((field_name, field_value))
    return "\n".join([f"**{name}:** {value}" for name, value in all_fields])


def create_submission_issue(submission: SubmissionMetadata, submitter: User) -> str:
    """Create a new GitHub issue for a submission and return the issue number as a string."""

    # Load the submission data into a Pydantic model for easier access to nested properties
    submission_py = schemas_submission.SubmissionMetadataSchema.model_validate(submission)

    # Build the body of the GitHub issue with relevant information from the submission
    study_form = submission_py.study_form
    fields = (
        ("Issue created from host", settings.host),
        ("Submitter", f"{submitter.name}, {submitter.orcid}"),
        ("Submission ID", str(submission_py.id)),
        ("PI name", study_form.piName),
        ("PI orcid", study_form.piOrcid),
    )
    optional_fields = (
        ("NCBI ID", study_form.NCBIBioProjectId),
        ("GOLD ID", study_form.GOLDStudyId),
        ("Alternative IDs", ", ".join(study_form.alternativeNames)),
    )

    # Create the GitHub issue and return the issue number.
    submission_issue = create_issue(
        title=f"NMDC Submission: {submission_py.id}",
        body=_format_body_list(fields, optional_fields),
        assignee=settings.github_issue_assignee,
    )
    return str(submission_issue.number)


def create_sample_set_issue(sample_set: SubmissionSampleSet, submitter: User) -> str:
    """Create a new GitHub issue for a sample set and return the issue number as a string."""

    # Load the submission and sample set data into Pydantic models for easier access to nested properties
    submission_py = schemas_submission.SubmissionMetadataSchema.model_validate(
        sample_set.submission_metadata
    )
    sample_set_py = schemas_submission.SubmissionSampleSet.model_validate(sample_set)

    multiomics_form = sample_set_py.multi_omics_form

    fields = (
        ("Issue created from host", settings.host),
        ("Submitter", f"{submitter.name}, {submitter.orcid}"),
        ("Submission ID", str(submission_py.id)),
        ("Sample set ID", str(sample_set_py.id)),
        ("Sample set name", sample_set_py.name),
        ("Has data been generated", "Yes" if multiomics_form.dataGenerated else "No"),
        ("Status", sample_set_py.status),
        ("Data types", ", ".join(multiomics_form.omicsProcessingTypes)),
        ("Sample type", ", ".join(sample_set_py.templates)),
        ("Number of samples in set", str(sample_set.sample_count)),
    )
    optional_fields = (
        ("JGI ID", multiomics_form.JGIStudyId),
        ("EMSL ID", multiomics_form.studyNumber),
    )

    # Create the sample set issue
    sample_set_issue = create_issue(
        title=f"NMDC Submission Sample Set: {submission_py.id} / {sample_set.name}",
        body=_format_body_list(fields, optional_fields),
        assignee=settings.github_issue_assignee,
    )

    # Look up the submission issue, add the sample set issue as a linked issue, and reopen
    # it if necessary. If the submission has no associated GitHub issue, log a warning and
    # skip linking.
    if submission_py.github_issue is not None:
        submission_issue = get_issue(submission_py.github_issue)
        reopen_issue(submission_issue)
        submission_issue.add_sub_issue(sample_set_issue)
    else:
        logger.warning(
            f"Submission {submission_py.id} has no associated GitHub issue; cannot link sample set issue to submission issue."
        )

    return str(sample_set_issue.number)


def add_sample_set_resubmit_comment(sample_set: SubmissionSampleSet, submitter: User) -> None:
    """Add a comment to the sample set issue indicating that the sample set was resubmitted."""

    comment_body = f"""
## 🔄 Submission Resubmitted

**Resubmitted by:** {submitter.name} ({submitter.orcid})
**Status:** {sample_set.status}

The submission has been updated and resubmitted for review.
        """.strip()

    if sample_set.github_issue is None:
        logger.warning(
            f"Sample set {sample_set.id} has no associated GitHub issue; cannot add resubmission comment."
        )
        return

    sample_set_issue = get_issue(sample_set.github_issue)
    add_issue_comment(sample_set_issue, comment_body)
    reopen_issue(sample_set_issue)

    if sample_set.submission_metadata.github_issue is not None:
        submission_issue = get_issue(sample_set.submission_metadata.github_issue)
        reopen_issue(submission_issue)
    else:
        logger.warning(
            f"Submission {sample_set.submission_metadata.id} has no associated GitHub issue; "
            f"cannot reopen submission issue when resubmitting sample set."
        )
