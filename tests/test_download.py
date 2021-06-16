from fastapi.testclient import TestClient
from sqlalchemy.orm.session import Session

from nmdc_server import fakes, query


def test_bulk_download_query(db: Session):
    sample = fakes.BiosampleFactory()
    op1 = fakes.OmicsProcessingFactory(biosample=sample)
    fakes.OmicsProcessingFactory(biosample=sample)

    raw1 = fakes.DataObjectFactory(omics_processing=op1)
    op1.outputs.append(raw1)

    metag = fakes.MetagenomeAnnotationFactory(omics_processing=op1)
    metag_output = fakes.DataObjectFactory(omics_processing=op1)
    metag.outputs.append(metag_output)

    db.commit()

    qs = query.DataObjectQuerySchema()
    rows = qs.execute(db).all()
    assert len(rows) == 2
    assert qs.aggregate(db) == {
        "size": raw1.file_size_bytes + metag_output.file_size_bytes,
        "count": 2,
    }

    qs = query.DataObjectQuerySchema(data_object_filter=[{"workflow": "nmdc:RawData"}])
    rows = qs.execute(db).all()
    assert [raw1.id] == [d.id for d in rows]
    assert qs.aggregate(db) == {"size": raw1.file_size_bytes, "count": 1}


def test_generate_bulk_download(db: Session, client: TestClient, token):
    sample = fakes.BiosampleFactory()
    op1 = fakes.OmicsProcessingFactory(biosample=sample)
    fakes.OmicsProcessingFactory(biosample=sample)

    raw1 = fakes.DataObjectFactory(
        omics_processing=op1, url="https://data.microbiomedata.org/data/raw"
    )
    op1.outputs.append(raw1)

    metag = fakes.MetagenomeAnnotationFactory(omics_processing=op1)
    metag_output = fakes.DataObjectFactory(
        omics_processing=op1, url="https://data.microbiomedata.org/data/metag"
    )
    metag.outputs.append(metag_output)

    db.commit()

    resp = client.post("/api/bulk_download")
    print(resp.content)
    assert resp.status_code == 201
    assert resp.json()["id"]
    id_ = resp.json()["id"]

    resp = client.post("/api/bulk_download/summary")
    assert resp.status_code == 200
    assert resp.json()["count"] == 2

    resp = client.get(f"/api/bulk_download/{id_}")
    assert resp.status_code == 200
    assert b"/raw" in resp.content and b"/metag" in resp.content


def test_generate_bulk_download_filtered(db: Session, client: TestClient, token):
    sample = fakes.BiosampleFactory()
    op1 = fakes.OmicsProcessingFactory(biosample=sample)
    fakes.OmicsProcessingFactory(biosample=sample)

    raw1 = fakes.DataObjectFactory(
        omics_processing=op1, url="https://data.microbiomedata.org/data/raw"
    )
    op1.outputs.append(raw1)

    metag = fakes.MetagenomeAnnotationFactory(omics_processing=op1)
    metag_output = fakes.DataObjectFactory(
        omics_processing=op1, url="https://data.microbiomedata.org/data/metag"
    )
    metag.outputs.append(metag_output)

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

    resp = client.get(f"/api/bulk_download/{id_}")
    assert resp.status_code == 200
    assert b"/raw" not in resp.content and b"/metag" in resp.content
