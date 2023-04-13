from starlette.testclient import TestClient

from nmdc_server import fakes
from nmdc_server.auth import Token
from nmdc_server.config import settings


def assert_status(response: Response, status: int = 200):
    __tracebackhide__ = True
    if response.headers["Content-Type"] != "application/json":
        print(response.content)
    elif response.status_code != status:
        print(json.dumps(response.json(), indent=2))
    assert response.status_code == status, "Invalid response code"


def test_login(client: TestClient):
    resp = client.request(method="get", url="/login", allow_redirects=False)

    assert resp.status_code == 302
    assert resp.next.url.startswith(settings.oauth_authorization_endpoint)  # type: ignore


def test_current_user(client: TestClient, token: Token):
    resp = client.get("/api/me")
    assert_status(resp)
    assert resp.json() == token.name


def test_logout(client: TestClient, token: Token):
    client.get("/logout")
    resp = client.get("/api/me")
    assert resp.json() == None


def test_admin_required(client: TestClient):
    resp = client.post("/api/jobs/ping")
    assert resp.status_code == 401


def test_login_required(db, client: TestClient):
    fakes.DataObjectFactory(id="nmdc:id")
    db.commit()

    resp = client.get("/api/data_object/nmdc:id/download")
    assert resp.status_code == 401
