from datetime import datetime

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm.session import Session

from nmdc_server import fakes, query
from nmdc_server.binning import DateBinResolution


@pytest.fixture
def biosamples(db: Session):
    depths = [1, 2, 3, 11, 12, 22]
    dates = [
        datetime(2020, 1, 1),
        datetime(2020, 1, 2),
        datetime(2020, 1, 8),
        datetime(2020, 1, 3),
        datetime(2020, 2, 9),
        datetime(2020, 2, 10),
    ]
    for depth, date in zip(depths, dates):
        fakes.BiosampleFactory(depth=depth, collection_date=date)
    db.commit()


def test_range_bins(db: Session, biosamples):
    q = query.BiosampleQuerySchema()
    bins, result = q.binned_facet(db, "depth", minimum=0, maximum=30, num_bins=3)
    assert bins == [0, 10, 20, 30]
    assert result == {0: 3, 1: 2, 2: 1}


def test_range_bins_default_min_max(db: Session, biosamples):
    q = query.BiosampleQuerySchema()
    bins, result = q.binned_facet(db, "depth", num_bins=3)
    assert bins == [1, 8, 15, 22]
    assert result == {0: 3, 1: 2, 2: 1}


def test_date_range_bins_week(db: Session, biosamples):
    q = query.BiosampleQuerySchema()
    bins, result = q.binned_facet(db, "collection_date", resolution=DateBinResolution.week)
    print(bins)
    assert len(bins) == 8
    assert bins[0] <= datetime(2020, 1, 1)  # type: ignore
    assert result == {0: 3, 1: 1, 6: 2}


def test_date_range_bins_month(db: Session, biosamples):
    q = query.BiosampleQuerySchema()
    bins, result = q.binned_facet(db, "collection_date", resolution=DateBinResolution.month)
    assert len(bins) == 3
    assert bins[0] <= datetime(2020, 1, 1)  # type: ignore
    assert result == {0: 4, 1: 2}


def test_date_range_bins_year(db: Session, biosamples):
    q = query.BiosampleQuerySchema()
    bins, result = q.binned_facet(db, "collection_date", resolution=DateBinResolution.year)
    assert len(bins) == 2
    assert result == {0: 6}


def test_filtered_bins(db: Session, biosamples):
    q = query.BiosampleQuerySchema(
        conditions=[
            {
                "table": "biosample",
                "field": "depth",
                "op": "<",
                "value": 20,
            }
        ]
    )
    bins, result = q.binned_facet(db, "depth", num_bins=2)
    assert bins == [1, 6.5, 12]
    assert result == {0: 3, 1: 2}


def test_filtered_bins_api(client: TestClient, biosamples):
    resp = client.post(
        "/api/biosample/binned_facet",
        json={
            "attribute": "depth",
            "num_bins": 2,
            "conditions": [
                {
                    "table": "biosample",
                    "field": "depth",
                    "op": "<",
                    "value": 20,
                }
            ],
        },
    )
    assert resp.status_code == 200
    assert resp.json() == {
        "bins": [1, 6.5, 12],
        "facets": {"0": 3, "1": 2},
    }


def test_binned_api(client: TestClient, biosamples):
    resp = client.post("/api/biosample/binned_facet", json={"attribute": "depth", "num_bins": 3})
    assert resp.status_code == 200
    assert resp.json() == {
        "bins": [1, 8, 15, 22],
        "facets": {"0": 3, "1": 2, "2": 1},
    }


def test_binned_date_api(client: TestClient, biosamples):
    resp = client.post(
        "/api/biosample/binned_facet", json={"attribute": "collection_date", "resolution": "month"}
    )
    assert resp.status_code == 200
    assert len(resp.json()["bins"]) == 3
    assert resp.json()["facets"] == {"0": 4, "1": 2}


def test_invalid_date_api(client: TestClient, biosamples):
    resp = client.post(
        "/api/biosample/binned_facet", json={"attribute": "depth", "resolution": "month"}
    )
    assert resp.status_code == 400
