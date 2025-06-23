import json
from importlib.metadata import version
from itertools import product

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy.orm.session import Session
from starlette import status as http_status

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


def test_get_settings(client: TestClient):
    resp = client.get("/api/settings")
    assert_status(resp)


def test_get_version(client: TestClient):
    resp = client.get("/api/version")
    assert resp.status_code == 200

    body = resp.json()
    assert body["nmdc_server"] == nmdc_server.__version__
    assert body["nmdc_schema"] == version("nmdc-schema")
    assert body["nmdc_submission_schema"] == version("nmdc-submission-schema")


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
    """
    This test checks the `/api/stats` endpoint to ensure it returns the expected
    summary statistics about the database, including the number of studies,

    WFE data size bytes test case:
    - here we test that the WFE data size is calculated correctly
    - we create 10 data objects with increasing file sizes (1 byte to 10 bytes)
    - we associate these data objects with various workflow execution processes.
        this tests that data object from different processes are accounted for.
    - we check that data object are not double counted through connecting the
        same data object to multiple processes
    - we then check that the total size of the WFE output data is 55 bytes.
        this is the sum of the first 10 natural numbers (1 + 2 + ... + 10 = 55).
    """
    # TODO: This would be better queried against the real data
    for i in range(10):
        data_object = fakes.DataObjectFactory(file_size_bytes=i + 1)
        # Create some data objects that are not associated with any processes
        fakes.DataObjectFactory(file_size_bytes=i + 1)
        fakes.BiosampleFactory()
        fakes.MetagenomeAnnotationFactory(outputs=[data_object])
        fakes.MetagenomeAssemblyFactory(outputs=[data_object])
        fakes.MetaproteomicAnalysisFactory(outputs=[data_object])

    # Create some additional, interrelated studies.
    # Note: The database already contains 10 studies at this point, created elsewhere.
    study_a = fakes.StudyFactory()
    study_b = fakes.StudyFactory()
    study_c = fakes.StudyFactory()
    study_b.part_of = [study_a.id]
    study_c.part_of = [study_a.id, study_b.id]

    db.commit()
    assert_status(client.get("/api/summary"))

    resp = client.get("/api/stats")
    assert_status(resp)
    data = resp.json()
    assert data["studies"] == 13
    assert data["non_parent_studies"] == 11  # excludes studies A and B
    assert data["wfe_output_data_size_bytes"] == 55


def test_get_admin_stats_authorization(db: Session, client: TestClient, logged_in_user):
    """This test demonstrates that non-admin users cannot access the endpoint."""

    resp = client.get("/api/admin/stats")
    assert_status(resp, http_status.HTTP_403_FORBIDDEN)


def test_get_admin_stats(db: Session, client: TestClient, logged_in_admin_user):
    # Seed the database.
    for _ in range(10):
        fakes.UserFactory()
    db.commit()

    # Submit the HTTP request.
    resp = client.get("/api/admin/stats")

    # Assert that the response meets our expectations.
    # Note: The `logged_in_admin_user` fixture also created 1 User in the database.
    assert_status(resp, http_status.HTTP_200_OK)
    assert resp.json()["num_user_accounts"] == 11


def test_get_pi_image(db: Session, client: TestClient):
    pi = fakes.PrincipalInvestigator()
    fakes.StudyFactory(principal_investigator=pi, id="study1")
    db.commit()
    resp = client.get("/api/study/study1")
    assert_status(resp)

    resp = client.get(resp.json()["image_url"])
    assert_status(resp)
    assert resp.headers["Content-Type"] == "image/jpeg"


def test_get_study_image(db: Session, client: TestClient):
    fakes.StudyFactory(id="study1")
    db.commit()
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
        "data_generation",
    ],
)
def test_list_data_objects(db: Session, client: TestClient, endpoint: str):
    data_object = fakes.DataObjectFactory(id="do")
    biosample_input = fakes.BiosampleFactory(id="b")
    omics_processing = fakes.OmicsProcessingFactory(id="1")
    reads_qc = fakes.ReadsQCFactory(id="1")
    assembly = fakes.MetagenomeAssemblyFactory(id="1")
    annotation = fakes.MetagenomeAnnotationFactory(id="1")
    analysis = fakes.MetaproteomicAnalysisFactory(id="1")

    omics_processing.outputs = [data_object]
    omics_processing.biosample_inputs = [biosample_input]
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
