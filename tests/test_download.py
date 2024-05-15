from fastapi.testclient import TestClient
from sqlalchemy.orm.session import Session

from nmdc_server import fakes, query
from nmdc_server.data_object_filters import WorkflowActivityTypeEnum


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

    metag = fakes.MetagenomeAnnotationFactory(omics_processing=op1)
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
    assert qs.aggregate(db) == {
        "size": 0,
        "count": 0,
    }

    qs = query.DataObjectQuerySchema(data_object_filter=[{"workflow": "nmdc:RawData"}])
    rows = qs.execute(db).all()
    assert [raw1.id] == [d.id for d in rows]
    assert qs.aggregate(db) == {"size": raw1.file_size_bytes, "count": 1}

    qs = query.DataObjectQuerySchema(data_object_filter=[{"file_type": "ftype1"}])
    rows = qs.execute(db).all()
    assert [raw1.id] == [d.id for d in rows]
    assert qs.aggregate(db) == {"size": raw1.file_size_bytes, "count": 1}


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

    metag = fakes.MetagenomeAnnotationFactory(omics_processing=op1)
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


def test_generate_bulk_download_filtered(db: Session, client: TestClient, logged_in_user):
    sample = fakes.BiosampleFactory()
    op1 = fakes.OmicsProcessingFactory(biosample_inputs=[sample])
    fakes.OmicsProcessingFactory(biosample_inputs=[sample])

    raw1 = fakes.DataObjectFactory(
        url="https://data.microbiomedata.org/data/raw",
        omics_processing=op1,
        workflow_type=WorkflowActivityTypeEnum.raw_data.value,
    )
    op1.outputs.append(raw1)

    metag = fakes.MetagenomeAnnotationFactory(omics_processing=op1)
    metag_output = fakes.DataObjectFactory(
        url="https://data.microbiomedata.org/data/metag",
        omics_processing=op1,
        workflow_type=WorkflowActivityTypeEnum.metagenome_annotation.value,
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
