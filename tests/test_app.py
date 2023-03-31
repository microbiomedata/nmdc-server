import json
from itertools import product

import pytest
from fastapi.testclient import TestClient
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
    resp = client.get("/api/openapi.json")
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
    condition["table"] = "biosample"
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


def test_get_study_image(db: Session, client: TestClient):
    fakes.StudyFactory(id="study1")
    db.commit()
    resp1 = client.get("/api/study/study1")
    assert_status(resp1)
    resp = client.get("/api/study/study1/image")
    assert_status(resp)
    assert resp.headers["Content-Type"] == "image/jpeg"


def test_get_environmental_aggregation(db: Session, client: TestClient):
    for _ in range(10):
        fakes.BiosampleFactory()

    assert_status(client.post("/api/environment/sankey"))
    resp = client.post(
        "/api/environment/sankey",
        json={
            "conditions": [
                {
                    "table": "study",
                    "field": "id",
                    "value": "not a study",
                }
            ]
        },
    )
    assert_status(resp)
    assert resp.json() == []

    assert_status(client.post("/api/environment/geospatial"))
    resp = client.post(
        "/api/environment/geospatial",
        json={
            "conditions": [
                {
                    "table": "study",
                    "field": "id",
                    "value": "not a study",
                }
            ]
        },
    )
    assert_status(resp)
    assert resp.json() == []


@pytest.mark.parametrize(
    "endpoint",
    [
        "omics_processing",
    ],
)
def test_list_data_objects(db: Session, client: TestClient, endpoint: str):
    data_object = fakes.DataObjectFactory(id="do")
    omics_processing = fakes.OmicsProcessingFactory(id="1")
    reads_qc = fakes.ReadsQCFactory(id="1")
    assembly = fakes.MetagenomeAssemblyFactory(id="1")
    annotation = fakes.MetagenomeAnnotationFactory(id="1")
    analysis = fakes.MetaproteomicAnalysisFactory(id="1")

    omics_processing.outputs = [data_object]
    reads_qc.outputs = [data_object]
    assembly.outputs = [data_object]
    annotation.outputs = [data_object]
    analysis.outputs = [data_object]
    db.commit()

    resp = client.get(f"/api/{endpoint}/1/outputs")
    assert_status(resp)
    assert ["do"] == [r["id"] for r in resp.json()]


@pytest.fixture
def gold_tree_biosamples(db):
    samples = []
    iterator = product(
        range(2),
        range(2),
        range(2),
        range(2),
        range(2),
    )
    for item in iterator:
        id_ = "_".join([str(i) for i in item])
        samples.append(
            fakes.BiosampleFactory(
                id=id_,
                ecosystem=f"ecosystem_{item[0]}",
                ecosystem_category=f"category_{item[1]}",
                ecosystem_type=f"type_{item[2]}",
                ecosystem_subtype=f"subtype_{item[3]}",
                specific_ecosystem=f"specific_{item[4]}",
            )
        )
    db.commit()
    yield samples


def _make_tree_query(client, query):
    resp = client.post(
        "/api/biosample/search",
        json={
            "conditions": query,
        },
    )
    assert_status(resp)
    return resp.json()


def test_gold_tree_empty_query(gold_tree_biosamples, client: TestClient):
    query = [{"table": "biosample", "field": "gold_tree", "op": "tree", "value": []}]
    data = _make_tree_query(client, query)
    assert data["count"] == len(gold_tree_biosamples)


def test_gold_tree_simple_query(gold_tree_biosamples, client: TestClient):
    query = [
        {
            "table": "biosample",
            "field": "gold_tree",
            "op": "tree",
            "value": [
                {
                    "ecosystem": "ecosystem_0",
                }
            ],
        }
    ]
    data = _make_tree_query(client, query)
    assert data["count"] == len(gold_tree_biosamples) / 2
    for d in data["results"]:
        assert d["id"].startswith("0_")


def test_gold_tree_nested_query(gold_tree_biosamples, client: TestClient):
    query = [
        {
            "table": "biosample",
            "field": "gold_tree",
            "op": "tree",
            "value": [
                {
                    "ecosystem": "ecosystem_0",
                    "ecosystem_category": "category_0",
                    "ecosystem_type": "type_0",
                }
            ],
        }
    ]
    data = _make_tree_query(client, query)
    assert data["count"] == len(gold_tree_biosamples) / 8
    for d in data["results"]:
        assert d["id"].startswith("0_0_0_")


def test_gold_tree_complex_query(gold_tree_biosamples, client: TestClient):
    query = [
        {
            "table": "biosample",
            "field": "gold_tree",
            "op": "tree",
            "value": [
                {
                    "ecosystem": "ecosystem_0",
                    "ecosystem_category": "category_0",
                    "ecosystem_type": "type_0",
                    "ecosystem_subtype": "subtype_0",
                    "specific_ecosystem": "specific_0",
                },
                {
                    "ecosystem": "ecosystem_0",
                    "ecosystem_category": "category_0",
                    "ecosystem_type": "type_1",
                    "ecosystem_subtype": "subtype_0",
                    "specific_ecosystem": "specific_0",
                },
                {
                    "ecosystem": "ecosystem_0",
                    "ecosystem_category": "category_0",
                    "ecosystem_type": "type_1",
                    "ecosystem_subtype": "subtype_1",
                },
            ],
        }
    ]
    data = _make_tree_query(client, query)
    assert {d["id"] for d in data["results"]} == {
        "0_0_0_0_0",
        "0_0_1_0_0",
        "0_0_1_1_0",
        "0_0_1_1_1",
    }
