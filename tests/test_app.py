import json

from fastapi.testclient import TestClient
import pytest
from requests.models import Response
from sqlalchemy.orm.session import Session

import nmdc_server
from nmdc_server import fakes


def assert_status(response: Response, status: int = 200):
    __tracebackhide__ = True
    if response.headers["Content-Type"] != "application/json":
        print(response.content)
    elif response.status_code != status:
        print(json.dumps(response.json(), indent=2))
    assert response.status_code == status, "Invalid response code"


def test_api_spec(client: TestClient):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert resp.json()["info"]["version"] == nmdc_server.__version__


@pytest.mark.parametrize(
    "condition,expected",
    [
        ({"field": "key1", "value": "value1", "op": "=="}, {"sample1", "sample2"}),
        ({"field": "key2", "value": "value2", "op": "=="}, {"sample1"}),
        ({"field": "key2", "value": "value", "op": ">"}, {"sample1", "sample2"}),
        ({"field": "key2", "value": "value", "op": "<"}, set()),
        ({"field": "key2", "value": "value2", "op": "!="}, {"sample2"}),
    ],
)
def test_api_query(db: Session, client: TestClient, condition, expected):
    fakes.BiosampleFactory(id="sample1", annotations={"key1": "value1", "key2": "value2"})
    fakes.BiosampleFactory(id="sample2", annotations={"key1": "value1", "key2": "value3"})
    for _ in range(10):
        fakes.BiosampleFactory()
    db.commit()

    resp = client.post("/api/biosample/search", json={"conditions": [condition]})
    assert_status(resp)
    results = resp.json()["results"]
    assert {s["id"] for s in results} == expected


def test_api_faceting(db: Session, client: TestClient):
    fakes.BiosampleFactory(id="sample1", annotations={"key1": "value1", "key2": "value2"})
    fakes.BiosampleFactory(id="sample2", annotations={"key1": "value1", "key2": "value3"})
    fakes.BiosampleFactory(id="sample3", annotations={"key1": "value4", "key2": "value2"})
    db.commit()

    resp = client.post("/api/biosample/facet", json={"conditions": [], "attribute": "key1"})
    assert_status(resp)
    assert resp.json()["facets"] == {"value1": 2, "value4": 1}

    resp = client.post("/api/biosample/facet", json={"conditions": [], "attribute": "key2"})
    assert_status(resp)
    assert resp.json()["facets"] == {"value2": 2, "value3": 1}


def test_api_summary(db: Session, client: TestClient):
    # TODO: This would be better queried against the real data
    for _ in range(10):
        fakes.BiosampleFactory()
        fakes.MetagenomeAnnotationFactory()
        fakes.MetagenomeAssemblyFactory()
        fakes.MetaproteomicAnalysisFactory()
        fakes.DataObjectFactory()
    db.commit()
    assert_status(client.get("/api/summary"))
    assert_status(client.get("/api/stats"))


def test_get_pi_image(db: Session, client: TestClient):
    pi = fakes.PrincipalInvestigator()
    fakes.StudyFactory(principal_investigator=pi, id="study1")
    db.commit()
    resp = client.get("/api/study/study1")
    assert_status(resp)

    resp = client.get(resp.json()["principal_investigator_image_url"])
    assert_status(resp)
    assert resp.headers["Content-Type"] == "image/jpeg"


def test_get_sankey_aggregation(db: Session, client: TestClient):
    for _ in range(10):
        fakes.BiosampleFactory()
    assert_status(client.post("/api/environment/sankey"))
    resp = client.post(
        "/api/environment/sankey",
        json={"conditions": [{"table": "study", "field": "id", "value": "not a study",}]},
    )
    assert_status(resp)
    assert resp.json() == []
