import json
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm.session import Session
from starlette.testclient import TestClient

from nmdc_server import fakes
from nmdc_server.auth import Token
from nmdc_server.models import SubmissionEditorRole, SubmissionRole
from nmdc_server.schemas_submission import SubmissionMetadataSchema


def test_list_submissions(db: Session, client: TestClient, token: Token, logged_in_user):
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    db.commit()

    response = client.request(method="GET", url="/api/metadata_submission")
    assert response.status_code == 200
    assert response.json()["results"][0]["id"] == str(submission.id)


def test_try_edit_locked_submission(db: Session, client: TestClient, token: Token, logged_in_user):
    # Locked by a random user at utcnow by default
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user,
        author_orcid=logged_in_user.orcid,
        locked_by=fakes.UserFactory(),
        lock_updated=datetime.utcnow(),
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    payload = SubmissionMetadataSchema(**submission.__dict__).json()
    db.commit()

    response = client.request(
        method="patch",
        url=f"/api/metadata_submission/{submission.id}",
        json=json.loads(payload),
    )
    assert response.status_code == 400


def test_try_edit_expired_locked_submission(
    db: Session, client: TestClient, token: Token, logged_in_user
):
    # initialize test submission with expired lock
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user,
        author_orcid=logged_in_user.orcid,
        locked_by=fakes.UserFactory(),
        lock_updated=datetime.utcnow() - timedelta(hours=1),
    )
    payload = SubmissionMetadataSchema(**submission.__dict__).json()
    db.commit()

    response = client.request(
        method="patch", url=f"/api/metadata_submission/{submission.id}", json=json.loads(payload)
    )
    assert response.status_code == 200


def test_try_edit_locked_by_current_user_submission(
    db: Session, client: TestClient, token: Token, logged_in_user
):
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user,
        author_orcid=logged_in_user.orcid,
        locked_by=logged_in_user,
        lock_updated=datetime.utcnow(),
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    payload = SubmissionMetadataSchema(**submission.__dict__).json()
    db.commit()

    response = client.request(
        method="patch", url=f"/api/metadata_submission/{submission.id}", json=json.loads(payload)
    )
    assert response.status_code == 200


def test_submission_list_with_roles(db: Session, client: TestClient, token: Token, logged_in_user):
    user_a = fakes.UserFactory()
    submission_a = fakes.MetadataSubmissionFactory(author=user_a, author_orcid=user_a.orcid)
    fakes.MetadataSubmissionFactory(author=logged_in_user, author_orcid=logged_in_user.orcid)
    fakes.MetadataSubmissionFactory(author=user_a, author_orcid=user_a.orcid)
    db.commit()
    fakes.SubmissionRoleFactory(
        submission=submission_a,
        submission_id=submission_a.id,
        user_orcid=logged_in_user.orcid,
    )
    db.commit()
    response = client.request(method="get", url="/api/metadata_submission")
    assert response.status_code == 200

    results = response.json()["results"]
    allowed_submission_ids = [result["id"] for result in results]
    expected_ids = [str(submission_a.id)]
    assert all([submission_id in expected_ids for submission_id in allowed_submission_ids])
    assert len(results) == 1


@pytest.mark.parametrize("role,code", [(SubmissionEditorRole.owner, 200), (None, 403)])
def test_get_submission_with_roles(
    db: Session, client: TestClient, token: Token, logged_in_user, role, code
):
    if role == SubmissionEditorRole.owner:
        submission = fakes.MetadataSubmissionFactory()
        db.commit()
        role = fakes.SubmissionRoleFactory(
            submission=submission, submission_id=submission.id, user_orcid=logged_in_user.orcid
        )
    else:
        submission = fakes.MetadataSubmissionFactory()
    db.commit()
    response = client.request(method="get", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == code


@pytest.mark.parametrize("role,code", [(SubmissionEditorRole.owner, 200), (None, 403)])
def test_edit_submission_with_roles(
    db: Session, client: TestClient, token: Token, logged_in_user, role, code
):
    if role == SubmissionEditorRole.owner:
        submission = fakes.MetadataSubmissionFactory()
        payload = SubmissionMetadataSchema(**submission.__dict__).json()
        db.commit()
        role = fakes.SubmissionRoleFactory(
            submission=submission, submission_id=submission.id, user_orcid=logged_in_user.orcid
        )
    else:
        submission = fakes.MetadataSubmissionFactory()
        payload = SubmissionMetadataSchema(**submission.__dict__).json()
    db.commit()
    response = client.request(
        method="patch", url=f"/api/metadata_submission/{submission.id}", json=json.loads(payload)
    )
    assert response.status_code == code


def test_owner_role_created_for_pi(db: Session, client: TestClient, token: Token, logged_in_user):
    pi_orcid = fakes.Faker("pystr")
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    fakes.SubmissionRoleFactory(
        submission=submission, submission_id=submission.id, user_orcid=logged_in_user.orcid
    )
    payload = SubmissionMetadataSchema(**submission.__dict__)
    db.commit()

    payload.metadata_submission.studyForm.piOrcid = str(pi_orcid)
    response = client.request(
        method="patch",
        url=f"/api/metadata_submission/{submission.id}",
        json=json.loads(payload.json()),
    )
    assert response.status_code == 200

    roles = db.query(SubmissionRole)
    assert roles.count() == 2

    role = roles.filter(SubmissionRole.user_orcid == str(pi_orcid)).first()
    assert role is not None
    assert role.user_orcid == str(pi_orcid)
    assert role.submission_id == submission.id
    assert SubmissionEditorRole(role.role) == SubmissionEditorRole.owner
