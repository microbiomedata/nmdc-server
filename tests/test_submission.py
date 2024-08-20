import json
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm.session import Session
from starlette.testclient import TestClient

from nmdc_server import fakes
from nmdc_server.models import SubmissionEditorRole, SubmissionRole
from nmdc_server.schemas_submission import SubmissionMetadataSchema, SubmissionMetadataSchemaPatch


def test_list_submissions(db: Session, client: TestClient, logged_in_user):
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    db.commit()

    response = client.request(method="GET", url="/api/metadata_submission")
    assert response.status_code == 200
    assert response.json()["results"][0]["id"] == str(submission.id)


def test_get_metadata_submissions_report_as_non_admin(
    db: Session, client: TestClient, logged_in_user
):
    response = client.request(method="GET", url="/api/metadata_submission/report")
    assert response.status_code == 403


def test_get_metadata_submissions_report_as_admin(
    db: Session, client: TestClient, logged_in_admin_user
):
    logged_in_user = logged_in_admin_user  # allows us to reuse some code snippets
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )

    # TODO: Create additional submissions.
    db.commit()

    # TODO: Check additional aspects of the HTTP response.
    response = client.request(method="GET", url="/api/metadata_submission/report")
    assert response.status_code == 200


def test_try_edit_locked_submission(db: Session, client: TestClient, logged_in_user):
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
    payload = SubmissionMetadataSchema(**submission.__dict__).json(exclude_unset=True)
    db.commit()

    response = client.request(
        method="patch",
        url=f"/api/metadata_submission/{submission.id}",
        json=json.loads(payload),
    )
    assert response.status_code == 400


def test_try_edit_expired_locked_submission(db: Session, client: TestClient, logged_in_user):
    # initialize test submission with expired lock
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user,
        author_orcid=logged_in_user.orcid,
        locked_by=fakes.UserFactory(),
        lock_updated=datetime.utcnow() - timedelta(hours=1),
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    payload = SubmissionMetadataSchema(**submission.__dict__).json(exclude_unset=True)
    db.commit()

    response = client.request(
        method="patch", url=f"/api/metadata_submission/{submission.id}", json=json.loads(payload)
    )
    assert response.status_code == 200


def test_try_edit_locked_by_current_user_submission(
    db: Session, client: TestClient, logged_in_user
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
    payload = SubmissionMetadataSchema(**submission.__dict__).json(exclude_unset=True)
    db.commit()

    response = client.request(
        method="patch", url=f"/api/metadata_submission/{submission.id}", json=json.loads(payload)
    )
    assert response.status_code == 200


def test_submission_list_with_roles(db: Session, client: TestClient, logged_in_user):
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
def test_get_submission_with_roles(db: Session, client: TestClient, logged_in_user, role, code):
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
def test_edit_submission_with_roles(db: Session, client: TestClient, logged_in_user, role, code):
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


def test_create_role_on_patch(db: Session, client: TestClient, logged_in_user):
    pi_orcid = fakes.Faker("pystr")
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    fakes.SubmissionRoleFactory(
        submission=submission, submission_id=submission.id, user_orcid=logged_in_user.orcid
    )
    payload = SubmissionMetadataSchemaPatch(**submission.__dict__)
    db.commit()

    payload.permissions = {str(pi_orcid): SubmissionEditorRole.owner.value}
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


@pytest.mark.parametrize("samples_only,code", [(True, 200), (False, 403)])
def test_piecewise_patch_metadata_contributor(
    db: Session, client: TestClient, logged_in_user, samples_only, code
):
    user = fakes.UserFactory()
    submission = fakes.MetadataSubmissionFactory(author=user, author_orcid=user.orcid)
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.metadata_contributor,
    )
    full_payload = SubmissionMetadataSchemaPatch(**submission.__dict__)
    db.commit()

    if samples_only:
        request_dict = {
            "metadata_submission": {"sampleData": full_payload.metadata_submission.sampleData}
        }
        request_payload = SubmissionMetadataSchemaPatch(**request_dict).json(exclude_unset=True)
    else:
        request_payload = full_payload.json()

    # Logged in user should not be able to submit full payload because it contains non-sample data
    response = client.request(
        method="patch",
        url=f"/api/metadata_submission/{submission.id}",
        json=json.loads(request_payload),
    )
    assert response.status_code == code


def test_delete_role_on_patch(db: Session, client: TestClient, logged_in_user):
    user_orcid = fakes.Faker("pystr")
    pi_orcid = fakes.Faker("pystr")
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=pi_orcid,
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=user_orcid,
        role=SubmissionEditorRole.viewer,
    )
    payload = SubmissionMetadataSchemaPatch(**submission.__dict__)
    db.commit()

    payload.permissions = {}

    response = client.request(
        method="patch",
        url=f"/api/metadata_submission/{submission.id}",
        json=json.loads(payload.json()),
    )
    assert response.status_code == 200
    roles = db.query(SubmissionRole)
    # logged_in_user's, pi's owner roles should still exist
    assert roles.count() == 2
    assert all([role.role == SubmissionEditorRole.owner for role in roles.all()])


def test_update_role_on_patch(db: Session, client: TestClient, logged_in_user):
    user_orcid = fakes.Faker("pystr")
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=user_orcid,
        role=SubmissionEditorRole.viewer,
    )
    payload = SubmissionMetadataSchemaPatch(**submission.__dict__)
    db.commit()

    payload.permissions = {str(user_orcid): SubmissionEditorRole.editor.value}
    response = client.request(
        method="patch",
        url=f"/api/metadata_submission/{submission.id}",
        json=json.loads(payload.json()),
    )
    assert response.status_code == 200
    roles = db.query(SubmissionRole).filter(SubmissionRole.user_orcid == str(user_orcid))
    assert roles.count() == 1
    role = roles.first()
    assert role and role.role == SubmissionEditorRole.editor


def test_delete_submission_by_owner(db: Session, client: TestClient, logged_in_user):
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    db.commit()

    # Verify that the DELETE request goes through
    response = client.request(method="DELETE", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 204

    # Verify that it's really gone
    response = client.request(method="GET", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 404


def test_delete_submission_by_non_owner(db: Session, client: TestClient, logged_in_user):
    user = fakes.UserFactory()
    submission = fakes.MetadataSubmissionFactory(author=user, author_orcid=user.orcid)
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.metadata_contributor,
    )
    db.commit()

    # Verify that a contributor cannot delete it
    response = client.request(method="DELETE", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 403

    # Verify that it is still there
    response = client.request(method="GET", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 200


def test_delete_submission_while_locked(db: Session, client: TestClient, logged_in_user):
    user = fakes.UserFactory()
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user,
        author_orcid=logged_in_user.orcid,
        locked_by=user,
        lock_updated=datetime.utcnow(),
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=user.orcid,
        role=SubmissionEditorRole.metadata_contributor,
    )
    db.commit()

    # Verify that a owner cannot delete while submission is locked
    response = client.request(method="DELETE", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 400

    # Verify that it is still there
    response = client.request(method="GET", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 200
