import json
from datetime import datetime, timedelta

from sqlalchemy.orm.session import Session
from starlette.testclient import TestClient

from nmdc_server import fakes
from nmdc_server.auth import Token
from nmdc_server.config import settings
from nmdc_server.schemas_submission import SubmissionMetadataSchema


def test_try_edit_locked_submission(db: Session, client: TestClient, token: Token):
    # Locked by a random user at utcnow by default
    submission = fakes.MetadataSubmissionFactory(
        locked_by=fakes.UserFactory(),
        lock_updated=datetime.utcnow(),
    )
    payload = SubmissionMetadataSchema(**submission.__dict__).json()
    db.commit()

    response = client.request(
        method="patch",
        url=f"/api/metadata_submission/{submission.id}",
        json=json.loads(payload),
    )
    assert response.status_code == 400


def test_try_edit_expired_locked_submission(db: Session, client: TestClient, token: Token):
    # initialize test submission with expired lock
    submission = fakes.MetadataSubmissionFactory(
        locked_by=fakes.UserFactory(), lock_updated=datetime.utcnow() - timedelta(hours=1)
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
        locked_by=logged_in_user,
        lock_updated=datetime.utcnow(),
    )
    payload = SubmissionMetadataSchema(**submission.__dict__).json()
    db.commit()

    response = client.request(
        method="patch", url=f"/api/metadata_submission/{submission.id}", json=json.loads(payload)
    )
    assert response.status_code == 200
