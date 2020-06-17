import re
from typing import Any, Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm.session import Session

from nmdc_server import fakes

_link_re = re.compile('<(?P<url>[^>]*)>; rel="(?P<name>[^ ]*)"')


def parse_links(response: Any) -> Dict[str, str]:
    link_dict: Dict[str, str] = {}
    for link in response.headers.get("links", "").split(", "):
        m = _link_re.match(link)
        if m:
            link_dict[m["name"]] = m["url"]
    return link_dict


def test_all_results(db: Session, client: TestClient):
    for _ in range(10):
        fakes.BiosampleFactory()
    db.commit()

    resp = client.post("/api/biosample/search?limit=20")
    assert len(resp.json()["results"]) == 10
    assert resp.json()["count"] == 10
    assert int(resp.headers["Resource-Count"]) == 10


def test_first_page(db: Session, client: TestClient):
    for _ in range(10):
        fakes.BiosampleFactory()
    db.commit()

    resp = client.post("/api/biosample/search?limit=9")
    assert len(resp.json()["results"]) == 9
    assert resp.json()["count"] == 10
    assert int(resp.headers["Resource-Count"]) == 10

    links = parse_links(resp)
    assert "offset=0" in links["first"]
    assert "offset=9" in links["next"]
    assert links["next"] == links["last"]


def test_last_page(db: Session, client: TestClient):
    for _ in range(10):
        fakes.BiosampleFactory()
    db.commit()

    resp = client.post("/api/biosample/search?limit=9&offset=9")
    assert len(resp.json()["results"]) == 1
    assert resp.json()["count"] == 10
    assert int(resp.headers["Resource-Count"]) == 10

    links = parse_links(resp)
    assert "offset=0" in links["first"]
    assert "next" not in links
    assert "offset=9" in links["last"]
