import nmdc_server


def test_api_spec(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert resp.json()["info"]["version"] == nmdc_server.__version__
