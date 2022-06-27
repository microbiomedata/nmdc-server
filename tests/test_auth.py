from starlette.testclient import TestClient

from nmdc_server import fakes
from nmdc_server.auth import Token
from nmdc_server.config import settings
from base64 import b64encode
import json

from json import JSONEncoder


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
    # session = b64encode(json.dumps(token, cls=TokenEncoder).encode("utf-8"))
    # print(session)
    # cookies = {"session": f"${str(session, 'utf-8')}"}
    # todo-  figure out what is the value after ==
    cookies = {
        "session": "eyJ0b2tlbiI6IHsiYWNjZXNzX3Rva2VuIjogIjY5YTNmN2I2LTU2NzAtNDE4OC1hZDI1LWE4NmZjYzU5NWMwMyIsICJ0b2tlbl90eXBlIjogImJlYXJlciIsICJyZWZyZXNoX3Rva2VuIjogImQwYWQzMTlmLTk4YjgtNDdlNC05ODY0LWI4YTRkNTFlNzFhYSIsICJleHBpcmVzX2luIjogNjMxMTM4NTE4LCAic2NvcGUiOiAiL2F1dGhlbnRpY2F0ZSIsICJuYW1lIjogIkRlZXBpa2EgIiwgIm9yY2lkIjogIjAwMDAtMDAwMi0xNDM2LTg4NDgiLCAiZXhwaXJlc19hdCI6IDIyODc0MjY4MzJ9fQ==.YrkUEA.-kln8-0tTPgoSsTLsTWaQQ6JYo8="
    }
    print(cookies)
    resp = client.get("/api/me", cookies=cookies)
    print(resp.headers)
    print(resp.headers["set-cookie"])
    assert resp.headers != None
