import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm.session import Session

from nmdc_server import fakes, query
from nmdc_server.data_object_filters import WorkflowActivityTypeEnum
from nmdc_server.config import Settings


def test_bulk_download_query(db: Session):
    sample = fakes.BiosampleFactory()
    op1 = fakes.OmicsProcessingFactory(biosample_inputs=[sample])
    fakes.OmicsProcessingFactory(biosample_inputs=[sample])

    raw1 = fakes.DataObjectFactory(
        url="https://data.microbiomedata.org/data/raw",
        omics_processing=op1,
        workflow_type=WorkflowActivityTypeEnum.raw_data.value,
        file_type="ftype1",
    )
    op1.outputs.append(raw1)

    metag = fakes.MetagenomeAnnotationFactory(was_informed_by=[op1])
    metag_output = fakes.DataObjectFactory(
        url="https://data.microbiomedata.org/data/metag",
        omics_processing=op1,
        workflow_type=WorkflowActivityTypeEnum.metagenome_annotation.value,
        file_type="ftype2",
    )
    metag.outputs.append(metag_output)

    db.commit()

    qs = query.DataObjectQuerySchema()
    rows = qs.execute(db).all()
    assert len(rows) == 0

    data_object_agg_obj = qs.aggregate(db)
    assert data_object_agg_obj.size == 0
    assert data_object_agg_obj.count == 0

    qs = query.DataObjectQuerySchema(data_object_filter=[{"workflow": "nmdc:RawData"}])
    rows = qs.execute(db).all()
    assert [raw1.id] == [d.id for d in rows]
    data_object_agg_obj = qs.aggregate(db)
    assert data_object_agg_obj.size == raw1.file_size_bytes
    assert data_object_agg_obj.count == 1

    qs = query.DataObjectQuerySchema(data_object_filter=[{"file_type": "ftype1"}])
    rows = qs.execute(db).all()
    assert [raw1.id] == [d.id for d in rows]
    data_object_agg_obj = qs.aggregate(db)
    assert data_object_agg_obj.size == raw1.file_size_bytes
    assert data_object_agg_obj.count == 1


def test_generate_bulk_download(db: Session, client: TestClient, logged_in_user):
    sample = fakes.BiosampleFactory()
    op1 = fakes.OmicsProcessingFactory(biosample_inputs=[sample])
    fakes.OmicsProcessingFactory(biosample_inputs=[sample])

    raw1 = fakes.DataObjectFactory(
        url="https://data.microbiomedata.org/data/raw",
        omics_processing=op1,
        workflow_type=WorkflowActivityTypeEnum.raw_data.value,
    )
    op1.outputs.append(raw1)

    metag = fakes.MetagenomeAnnotationFactory(was_informed_by=[op1])
    metag_output = fakes.DataObjectFactory(
        url="https://data.microbiomedata.org/data/metag",
        omics_processing=op1,
        workflow_type=WorkflowActivityTypeEnum.metagenome_annotation.value,
    )
    metag.outputs.append(metag_output)

    db.commit()

    resp = client.post("/api/bulk_download")
    print(resp.content)
    assert resp.status_code == 400

    resp = client.post("/api/bulk_download/summary")
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


def test_generate_bulk_download_filtered(
    db: Session, client: TestClient, logged_in_user, patch_zip_stream_service
):
    sample = fakes.BiosampleFactory()
    op1 = fakes.OmicsProcessingFactory(biosample_inputs=[sample])
    fakes.OmicsProcessingFactory(biosample_inputs=[sample])

    raw1 = fakes.DataObjectFactory(
        url="https://data.microbiomedata.org/data/raw",
        omics_processing=op1,
        workflow_type=WorkflowActivityTypeEnum.raw_data.value,
    )
    op1.outputs.append(raw1)

    metag = fakes.MetagenomeAnnotationFactory(was_informed_by=[op1])
    metag_output = fakes.DataObjectFactory(
        url="https://data.microbiomedata.org/data/metag",
        omics_processing=op1,
        workflow_type=WorkflowActivityTypeEnum.metagenome_annotation.value,
    )
    metag.outputs.append(metag_output)
    op1.outputs.append(metag_output)

    db.commit()

    filter = [
        {
            "workflow": "nmdc:MetagenomeAnnotation",
        }
    ]
    resp = client.post("/api/bulk_download", json={"data_object_filter": filter})
    assert resp.status_code == 201
    assert resp.json()["id"]
    id_ = resp.json()["id"]

    resp = client.post("/api/bulk_download/summary", json={"data_object_filter": filter})
    assert resp.status_code == 200
    assert resp.json()["count"] == 1

    # Verify that the bulk download can be accessed without authentication
    resp = client.get(f"/api/bulk_download/{id_}")
    del client.headers["Authorization"]
    assert resp.status_code == 200

    # Verify that the bulk download cannot be accessed a second time
    resp = client.get(f"/api/bulk_download/{id_}")
    assert resp.status_code == 410


@pytest.mark.parametrize(
    ("data_object_type", "expected_status_code"), [("Kraken2 Krona Plot", 200), ("foo", 400)]
)
def test_get_url_for_html_content_unauthenticated(
    db: Session,
    client: TestClient,
    data_object_type: str,
    expected_status_code: int,
):
    data_object = fakes.DataObjectFactory(
        url="https://data.microbiomedata.org/data/dob",
        workflow_type=WorkflowActivityTypeEnum.metagenome_assembly.value,
        file_type=data_object_type,
    )
    db.commit()
    resp = client.get(f"/api/data_object/{data_object.id}/get_html_content_url")
    assert resp.status_code == expected_status_code


@pytest.mark.parametrize(
    ("data_object_type", "expected_status_code"), [("Kraken2 Krona Plot", 200), ("foo", 400)]
)
def test_get_url_for_html_content_authenticated(
    db: Session,
    client: TestClient,
    logged_in_user,
    data_object_type: str,
    expected_status_code: int,
):
    data_object = fakes.DataObjectFactory(
        url="https://data.microbiomedata.org/data/dob",
        workflow_type=WorkflowActivityTypeEnum.metagenome_assembly.value,
        file_type=data_object_type,
    )
    db.commit()
    resp = client.get(f"/api/data_object/{data_object.id}/get_html_content_url")
    assert resp.status_code == expected_status_code


def test_download_data_object_without_url_replacement(
    db: Session, client: TestClient, logged_in_user
):
    """Test single data object download without URL replacement."""
    data_object = fakes.DataObjectFactory(
        url="https://data.microbiomedata.org/data/test_file.txt",
    )
    db.commit()

    resp = client.get(f"/api/data_object/{data_object.id}/download")
    assert resp.status_code == 200
    assert resp.json()["url"] == "https://data.microbiomedata.org/data/test_file.txt"


def test_download_data_object_with_url_replacement(
    db: Session, client: TestClient, logged_in_user, monkeypatch
):
    """Test single data object download with URL replacement."""
    # Set the environment variable for URL replacement
    monkeypatch.setenv(
        "NMDC_NERSC_SINGLE_DATA_URL_REPLACEMENT_PREFIX", "https://foo.example.com/bar"
    )

    # Need to reload settings to pick up the new environment variable
    from nmdc_server import crud

    original_settings = crud.Settings
    crud.Settings = lambda: Settings()

    try:
        data_object = fakes.DataObjectFactory(
            url="https://data.microbiomedata.org/data/test_file.txt",
        )
        db.commit()

        resp = client.get(f"/api/data_object/{data_object.id}/download")
        assert resp.status_code == 200
        assert resp.json()["url"] == "https://foo.example.com/bar/test_file.txt"
    finally:
        crud.Settings = original_settings


def test_download_data_object_non_nersc_url(
    db: Session, client: TestClient, logged_in_user, monkeypatch
):
    """Test single data object download with non-NERSC URL (should not be replaced)."""
    monkeypatch.setenv(
        "NMDC_NERSC_SINGLE_DATA_URL_REPLACEMENT_PREFIX", "https://foo.example.com/bar"
    )

    from nmdc_server import crud

    original_settings = crud.Settings
    crud.Settings = lambda: Settings()

    try:
        data_object = fakes.DataObjectFactory(
            url="https://other.example.com/data/test_file.txt",
        )
        db.commit()

        resp = client.get(f"/api/data_object/{data_object.id}/download")
        assert resp.status_code == 200
        # URL should not be replaced since it doesn't start with
        # https://data.microbiomedata.org/data
        assert resp.json()["url"] == "https://other.example.com/data/test_file.txt"
    finally:
        crud.Settings = original_settings
