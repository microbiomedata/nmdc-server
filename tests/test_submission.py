import json
from csv import DictReader
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm.session import Session
from starlette.testclient import TestClient

from nmdc_server import fakes
from nmdc_server.models import SubmissionEditorRole, SubmissionRole
from nmdc_server.schemas_submission import SubmissionMetadataSchema, SubmissionMetadataSchemaPatch


@pytest.fixture
def suggest_payload():
    return [
        {"row": 1, "data": {"foo": "bar", "lat_lon": "44.058648, -123.095277"}},
        {"row": 3, "data": {"elev": "0", "lat_lon": "44.046389 -123.051910"}},
        {"row": 4, "data": {"foo": "bar"}},
        {"row": 5, "data": {"lat_lon": "garbage foo bar"}},
    ]


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


def test_get_metadata_submissions_mixs(db: Session, client: TestClient, logged_in_user):
    # Create test submission
    # submission1 has "Submitted- Pending Review" as the status (this is the one we want)
    submission1 = fakes.MetadataSubmissionFactory(
        status="Submitted- Pending Review",
        metadata_submission={
            "sampleData": {
                "built_env_data": [
                    {
                        "samp_name": "Sample A",
                        "env_medium": "Medium A",
                        "env_broad_scale": "Broad Scale A",
                        "env_local_scale": "Local Scale A"
                    },
                    {
                        "samp_name": "Sample B",
                        "env_medium": "Medium B",
                        "env_broad_scale": "Broad Scale B",
                        "env_local_scale": "Local Scale B"
                    }
                ],
                "water_data": [
                    {
                        "samp_name": "Sample C",
                        "env_medium": "Medium C",
                        "env_broad_scale": "Broad Scale C",
                        "env_local_scale": "Local Scale C"
                    }
                ]
            },
            "packageName": "Env Pkg 1"
        }
    )
    db.commit()
    response = client.request(method="get", url="/api/metadata_submission/mixs_report")
    assert response.status_code == 200

    # Check that the reponse payload is a TSV and that the result has the correct
    # number of rows and information populated. The result should have 4 rows
    # including a header.
    # Reference: https://docs.python.org/3/library/csv.html#csv.DictReader

    fieldnames = [
        "Submission ID",
        "Status",
        "Sample Name",
        "Environmental Package/Extension",
        "Environmental Broad Scale",
        "Environmental Local Scale",
        "Environmental Medium",
    ]
    reader = DictReader(response.text.splitlines(), fieldnames=fieldnames, delimiter="\t")
    rows = [row for row in reader]
    assert len(rows) == 4  # including the header row

    header_row = rows[0]  # get the header row
    assert len(list(header_row.keys())) == len(fieldnames)

    data_row = rows[1]  # first data row (data about Sample A in submission1)
    assert data_row["Submission ID"] == str(submission1.id)
    assert data_row["Status"] == "Submitted- Pending Review"
    assert data_row["Sample Name"] == "Sample C"
    assert data_row["Environmental Package/Extension"] == "Env Pkg 1"
    assert data_row["Environmental Broad Scale"] == "Broad Scale C"
    assert data_row["Environmental Local Scale"] == "Local Scale C"
    assert data_row["Environmental Medium"] == "Medium C"

    data_row = rows[2]  # second data row (data about Sample B in submission1)
    assert data_row["Submission ID"] == str(submission1.id)
    assert data_row["Status"] == "Submitted- Pending Review"
    assert data_row["Sample Name"] == "Sample A"
    assert data_row["Environmental Package/Extension"] == "Env Pkg 1"
    assert data_row["Environmental Broad Scale"] == "Broad Scale A"
    assert data_row["Environmental Local Scale"] == "Local Scale A"
    assert data_row["Environmental Medium"] == "Medium A"

    data_row = rows[3]  # third data row (data about Sample C in submission1)
    assert data_row["Submission ID"] == str(submission1.id)
    assert data_row["Status"] == "Submitted- Pending Review"
    assert data_row["Sample Name"] == "Sample B"
    assert data_row["Environmental Package/Extension"] == "Env Pkg 1"
    assert data_row["Environmental Broad Scale"] == "Broad Scale B"
    assert data_row["Environmental Local Scale"] == "Local Scale B"
    assert data_row["Environmental Medium"] == "Medium B"


def test_get_metadata_submissions_report_as_non_admin(
    db: Session, client: TestClient, logged_in_user
):
    response = client.request(method="GET", url="/api/metadata_submission/report")
    assert response.status_code == 403


def test_get_metadata_submissions_report_as_admin(
    db: Session, client: TestClient, logged_in_admin_user
):
    now = datetime.utcnow()

    # Create two submissions, only one of which is owned by the logged-in user.
    logged_in_user = logged_in_admin_user  # allows us to reuse some code snippets
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user,
        author_orcid=logged_in_user.orcid,
        created=now,
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    other_user = fakes.UserFactory()
    other_submission = fakes.MetadataSubmissionFactory(
        author=other_user,
        author_orcid=other_user.orcid,
        created=now + timedelta(seconds=1),
        metadata_submission={
            "studyForm": {
                "studyName": "My study name",
                "piName": "My PI name",
                "piEmail": "My PI email",
            },
        },
        status="in-progress",
        source_client="field_notes",
    )
    db.commit()

    response = client.request(method="GET", url="/api/metadata_submission/report")
    assert response.status_code == 200

    # Confirm the response payload is a TSV file having the fields and values we expect;
    # i.e. below its header row, it has two data rows, each representing a submission,
    # ordered from most recently-created to least recently-created.
    # Reference: https://docs.python.org/3/library/csv.html#csv.DictReader
    fieldnames = [
        "Submission ID",
        "Author ORCID",
        "Author Name",
        "Study Name",
        "PI Name",
        "PI Email",
        "Source Client",
        "Status",
    ]
    reader = DictReader(response.text.splitlines(), fieldnames=fieldnames, delimiter="\t")
    rows = [row for row in reader]
    assert len(rows) == 3  # includes the header row

    header_row = rows[0]  # gets the header row
    assert len(list(header_row.keys())) == len(fieldnames)

    data_row = rows[1]  # gets the first data row (the most recently-created submission)
    assert data_row["Submission ID"] == str(other_submission.id)
    assert data_row["Author ORCID"] == other_user.orcid
    assert data_row["Author Name"] == other_user.name
    assert data_row["Study Name"] == "My study name"
    assert data_row["PI Name"] == "My PI name"
    assert data_row["PI Email"] == "My PI email"
    assert data_row["Source Client"] == "field_notes"
    assert data_row["Status"] == "in-progress"

    data_row = rows[2]  # gets the second data row
    assert data_row["Submission ID"] == str(submission.id)
    assert data_row["Author ORCID"] == logged_in_user.orcid
    assert data_row["Author Name"] == logged_in_user.name
    assert data_row["Study Name"] == ""
    assert data_row["PI Name"] == ""
    assert data_row["PI Email"] == ""
    assert data_row["Source Client"] == ""  # upstream faker lacks `source_client` attribute
    assert data_row["Status"] == "In Progress"  # matches value in upstream faker


def test_obtain_submission_lock(db: Session, client: TestClient, logged_in_user):
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

    # Should be able to successfully GET this submission and the lock should not be set
    response = client.request(method="get", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 200
    body = response.json()
    assert body.get("locked_by") is None

    # Attempt to acquire the lock
    response = client.request(method="put", url=f"/api/metadata_submission/{submission.id}/lock")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["locked_by"]["id"] == str(logged_in_user.id)

    # Verify that the lock is set
    response = client.request(method="get", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["locked_by"]["id"] == str(logged_in_user.id)


def test_cannot_acquire_lock_on_locked_submission(db: Session, client: TestClient, logged_in_user):
    locking_user = fakes.UserFactory()
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user,
        author_orcid=logged_in_user.orcid,
        locked_by=locking_user,
        lock_updated=datetime.utcnow(),
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    db.commit()

    # Attempt to acquire the lock, verify that it fails and reports the current lock holder
    response = client.request(method="put", url=f"/api/metadata_submission/{submission.id}/lock")
    assert response.status_code == 409
    body = response.json()
    assert body["success"] is False
    assert body["locked_by"]["id"] == str(locking_user.id)


def test_release_submission_lock(db: Session, client: TestClient, logged_in_user):
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
    db.commit()

    # Verify that the lock is set
    response = client.request(method="get", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["locked_by"]["id"] == str(logged_in_user.id)

    # Release the lock
    response = client.request(method="put", url=f"/api/metadata_submission/{submission.id}/unlock")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True

    # Verify that the lock is released
    response = client.request(method="get", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["locked_by"] is None


def test_cannot_release_other_users_submission_lock(
    db: Session, client: TestClient, logged_in_user
):
    locking_user = fakes.UserFactory()
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user,
        author_orcid=logged_in_user.orcid,
        locked_by=locking_user,
        lock_updated=datetime.utcnow(),
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    db.commit()

    # Attempt to release the lock, verify that it fails
    response = client.request(method="put", url=f"/api/metadata_submission/{submission.id}/unlock")
    assert response.status_code == 409
    body = response.json()
    assert body["success"] is False
    assert body["locked_by"]["id"] == str(locking_user.id)


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


def test_sync_submission_templates(db: Session, client: TestClient, logged_in_user):
    template = "foo"
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
    payload = json.loads(
        SubmissionMetadataSchemaPatch(**submission.__dict__).json(exclude_unset=True)
    )
    payload["metadata_submission"]["templates"] = [template]
    db.commit()

    _ = client.request(
        method="PATCH", url=f"/api/metadata_submission/{submission.id}", json=payload
    )
    response = client.request(method="GET", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 200
    assert len(response.json()["templates"]) == 1
    assert response.json()["templates"][0] == template


def test_sync_submission_study_name(db: Session, client: TestClient, logged_in_user):
    expected_val = "my study"
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
    payload = json.loads(
        SubmissionMetadataSchemaPatch(**submission.__dict__).json(exclude_unset=True)
    )
    payload["metadata_submission"]["studyForm"]["studyName"] = expected_val
    db.commit()

    _ = client.request(
        method="PATCH", url=f"/api/metadata_submission/{submission.id}", json=payload
    )
    response = client.request(method="GET", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 200
    assert response.json()["study_name"] == expected_val


def test_metadata_suggest(client: TestClient, suggest_payload, logged_in_user):
    response = client.request(
        method="POST", url="/api/metadata_submission/suggest", json=suggest_payload
    )
    assert response.status_code == 200
    assert response.json() == [
        {"type": "add", "row": 1, "slot": "elev", "value": "16.0"},
        {"type": "replace", "row": 3, "slot": "elev", "value": "16.0"},
    ]


def test_metadata_suggest_single_type(client: TestClient, suggest_payload, logged_in_user):
    response = client.request(
        method="POST",
        url="/api/metadata_submission/suggest?types=add",
        json=suggest_payload,
    )
    assert response.status_code == 200
    assert response.json() == [
        {"type": "add", "row": 1, "slot": "elev", "value": "16.0"},
    ]


def test_metadata_suggest_multiple_types(client: TestClient, suggest_payload, logged_in_user):
    response = client.request(
        method="POST",
        url="/api/metadata_submission/suggest?types=add&types=replace",
        json=suggest_payload,
    )
    assert response.status_code == 200
    assert response.json() == [
        {"type": "add", "row": 1, "slot": "elev", "value": "16.0"},
        {"type": "replace", "row": 3, "slot": "elev", "value": "16.0"},
    ]


def test_metadata_suggest_invalid_type(client: TestClient, suggest_payload, logged_in_user):
    response = client.request(
        method="POST",
        url="/api/metadata_submission/suggest?types=whatever",
        json=suggest_payload,
    )
    assert response.status_code == 422
