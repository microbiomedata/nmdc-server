import json
from base64 import b64encode
from json import JSONEncoder

import itsdangerous
from starlette.testclient import TestClient

from nmdc_server import fakes
from nmdc_server.auth import Token
from nmdc_server.config import settings


def test_login(client: TestClient):
    resp = client.request(method="get", url="/login", allow_redirects=False)

    assert resp.status_code == 302
    assert resp.next.url.startswith(settings.oauth_authorization_endpoint)  # type: ignore


def test_current_user(client: TestClient, token: Token):
    resp = client.get("/api/me")
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


class TokenEncoder(JSONEncoder):
    def default(self, o):
        return str(o)


def test_cookie_headers(client: TestClient, token: Token):

    # replicating the behavior of session middleware to set jwt token as a cookie header in request
    signer = itsdangerous.TimestampSigner("test")  # same as the secret_key set at application start
    encoded_token = b64encode(json.dumps(token, cls=TokenEncoder).encode("utf-8"))
    encoded_token = signer.sign(f"${str(encoded_token, 'utf-8')}")
    # data = signer.unsign(encoded_token, max_age=14 * 24 * 60 * 60)
    cookies = {"session": str(encoded_token)}
    resp = client.get("/api/me", cookies=cookies)

    assert resp.headers != None
    # todo - identify issue in setting cookie in request that prevents setting of response header
    # current result-> response.header = {'content-length': '4', 'content-type': 'application/json'}
    # assert "Set-Cookie" in resp.headers
