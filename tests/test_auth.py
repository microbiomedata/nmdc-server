from starlette.testclient import TestClient

from nmdc_server import fakes
from nmdc_server.config import Settings


def test_login(client: TestClient):
    settings = Settings()
    allowed_redirect_uri = settings.login_redirect_allow_origins.split(",")[0]
    resp = client.request(
        method="get",
        url=f"/auth/login?redirect_uri={allowed_redirect_uri}/whatever",
        allow_redirects=False,
    )

    assert resp.status_code == 302
    assert resp.next.url.startswith(settings.orcid_base_url),  # type: ignore


def test_current_user(client: TestClient, logged_in_user):
    resp = client.get("/api/me")
    body = resp.json()
    assert body["name"] == logged_in_user.name


def test_logout(client: TestClient, logged_in_user):
    logout_response = client.post("/auth/logout")
    logout_response.raise_for_status()
    resp = client.get("/api/me")
    assert resp.status_code == 401


def test_admin_required(client: TestClient):
    resp = client.post("/api/jobs/ping")
    assert resp.status_code == 401


def test_login_required(db, client: TestClient):
    fakes.DataObjectFactory(id="nmdc:id")
    db.commit()

    resp = client.get("/api/data_object/nmdc:id/download")
    assert resp.status_code == 401
