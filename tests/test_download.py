import io
import json
import zipfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm.session import Session

from nmdc_server import models, query
from nmdc_server.data_object_filters import WorkflowActivityTypeEnum
from nmdc_server.rocrate import generate_rocrate_for_bulk_download
from tests import fakes


def _metadata_zip_documents(response, filename: str) -> list[dict]:
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        return json.loads(archive.read(filename))


def test_metadata_download_filters_superseded_workflow_executions_and_outputs(
    db: Session, client: TestClient
):
    sample = fakes.BiosampleFactory()
    current_workflow = fakes.MetagenomeAnnotationFactory()
    superseded_workflow = fakes.MetagenomeAnnotationFactory(superseded_by=current_workflow.id)
    current_output = fakes.DataObjectFactory()
    superseded_output = fakes.DataObjectFactory()
    current_workflow.outputs.append(current_output)
    superseded_workflow.outputs.append(superseded_output)

    documents = [
        models.BiosampleRelatedDocument(
            id=current_workflow.id,
            biosample_ids=[sample.id],
            high_level_type="nmdc:WorkflowExecution",
            document={"id": current_workflow.id},
        ),
        models.BiosampleRelatedDocument(
            id=superseded_workflow.id,
            biosample_ids=[sample.id],
            high_level_type="nmdc:WorkflowExecution",
            document={"id": superseded_workflow.id, "superseded_by": current_workflow.id},
        ),
        models.BiosampleRelatedDocument(
            id=current_output.id,
            biosample_ids=[sample.id],
            high_level_type="nmdc:DataObject",
            document={"id": current_output.id},
        ),
        models.BiosampleRelatedDocument(
            id=superseded_output.id,
            biosample_ids=[sample.id],
            high_level_type="nmdc:DataObject",
            document={"id": superseded_output.id},
        ),
    ]
    db.add_all(documents)
    db.commit()

    request = {
        "endpoints": ["nmdc:DataObject", "nmdc:WorkflowExecution"],
        "include_superseded_workflow_executions": False,
    }
    response = client.post("/api/download_metadata", json=request)

    assert response.status_code == 200
    assert [doc["id"] for doc in _metadata_zip_documents(response, "data_objects.json")] == [
        current_output.id
    ]
    assert [doc["id"] for doc in _metadata_zip_documents(response, "workflow_executions.json")] == [
        current_workflow.id
    ]

    request["include_superseded_workflow_executions"] = True
    response = client.post("/api/download_metadata", json=request)

    assert response.status_code == 200
    assert {doc["id"] for doc in _metadata_zip_documents(response, "data_objects.json")} == {
        current_output.id,
        superseded_output.id,
    }
    assert {doc["id"] for doc in _metadata_zip_documents(response, "workflow_executions.json")} == {
        current_workflow.id,
        superseded_workflow.id,
    }


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


def test_generate_rocrate_for_bulk_download_includes_compact_related_graph(db: Session):
    documents = [
        models.BiosampleRelatedDocument(
            id="nmdc:sty-1",
            biosample_ids=["nmdc:bsm-1"],
            high_level_type="nmdc:Study",
            document={"id": "nmdc:sty-1", "type": "nmdc:Study"},
            downstream_neighbor_ids=["nmdc:bsm-1"],
        ),
        models.BiosampleRelatedDocument(
            id="nmdc:bsm-1",
            biosample_ids=["nmdc:bsm-1"],
            high_level_type="nmdc:Biosample",
            document={
                "id": "nmdc:bsm-1",
                "type": "nmdc:Biosample",
                "associated_studies": ["nmdc:sty-1"],
            },
            downstream_neighbor_ids=["nmdc:dgns-1"],
        ),
        models.BiosampleRelatedDocument(
            id="nmdc:dgns-1",
            biosample_ids=["nmdc:bsm-1"],
            high_level_type="nmdc:DataGeneration",
            document={
                "id": "nmdc:dgns-1",
                "type": "nmdc:DataGeneration",
                "has_input": ["nmdc:bsm-1"],
                "has_output": ["nmdc:dobj-raw"],
            },
            downstream_neighbor_ids=["nmdc:dobj-raw", "nmdc:wfrqc-1"],
        ),
        models.BiosampleRelatedDocument(
            id="nmdc:wfrqc-1",
            biosample_ids=["nmdc:bsm-1"],
            high_level_type="nmdc:WorkflowExecution",
            document={
                "id": "nmdc:wfrqc-1",
                "type": "nmdc:ReadQcAnalysis",
                "has_input": ["nmdc:dobj-raw"],
                "has_output": ["nmdc:dobj-1"],
            },
            downstream_neighbor_ids=["nmdc:dobj-1"],
        ),
        models.BiosampleRelatedDocument(
            id="nmdc:dobj-1",
            biosample_ids=["nmdc:bsm-1"],
            high_level_type="nmdc:DataObject",
            document={
                "id": "nmdc:dobj-1",
                "type": "nmdc:DataObject",
            },
            downstream_neighbor_ids=[],
        ),
        models.BiosampleRelatedDocument(
            id="nmdc:dobj-unrelated",
            biosample_ids=[],
            high_level_type="nmdc:DataObject",
            document={"id": "nmdc:dobj-unrelated", "type": "nmdc:DataObject"},
            downstream_neighbor_ids=[],
        ),
    ]
    db.add_all(documents)
    bulk_download = models.BulkDownload(orcid="0000", ip="127.0.0.1", conditions=[], filter=[])
    db.add(bulk_download)
    db.flush()

    crate = generate_rocrate_for_bulk_download(db, bulk_download, ["nmdc:dobj-1"])
    nodes = {node["@id"]: node for node in crate["@graph"]}

    assert "nmdc:dobj-1" not in nodes
    assert "nmdc:dobj-unrelated" not in nodes
    assert nodes["nmdc:bsm-1"]["isPartOf"] == [{"@id": "nmdc:sty-1"}]
    assert nodes["nmdc:bsm-1"]["subjectOf"] == [{"@id": "nmdc:dgns-1"}]
    assert nodes["nmdc:dgns-1"]["object"] == [{"@id": "nmdc:bsm-1"}]
    assert nodes["nmdc:dgns-1"]["result"] == [{"@id": "nmdc:wfrqc-1"}]
    assert nodes["nmdc:wfrqc-1"]["isBasedOn"] == [{"@id": "nmdc:dgns-1"}]


def test_bulk_download_rocrate_endpoint_returns_and_clears_cache(db: Session, client: TestClient):
    bulk_download = models.BulkDownload(
        orcid="0000",
        ip="127.0.0.1",
        conditions=[],
        filter=[],
        rocrate_metadata_cache={"@context": "test", "@graph": []},
    )
    db.add(bulk_download)
    db.commit()

    response = client.get(f"/api/bulk_download/{bulk_download.id}/ro-crate-metadata.json")

    assert response.status_code == 200
    assert response.json() == {"@context": "test", "@graph": []}
    db.expire_all()
    assert db.get(models.BulkDownload, bulk_download.id).rocrate_metadata_cache is None


def test_bulk_download_data_object_metadata_uses_archive_path(db: Session, client: TestClient):
    data_object = fakes.DataObjectFactory(
        id="nmdc:dobj-1",
        name="file.txt",
        url="https://data.microbiomedata.org/data/file.txt",
    )
    bulk_download = models.BulkDownload(orcid="0000", ip="127.0.0.1", conditions=[], filter=[])
    path = "data/nmdc_dgns-1/nmdc_wfrqc-1/file.txt"
    db.add(
        models.BulkDownloadDataObject(
            bulk_download=bulk_download,
            data_object=data_object,
            path=path,
        )
    )
    db.add(
        models.BiosampleRelatedDocument(
            id=data_object.id,
            biosample_ids=["nmdc:bsm-1"],
            high_level_type="nmdc:DataObject",
            document={"id": data_object.id, "name": data_object.name, "url": data_object.url},
            downstream_neighbor_ids=[],
        )
    )
    db.commit()

    response = client.get(f"/api/bulk_download/{bulk_download.id}/metadata/data_objects.json")

    assert response.status_code == 200
    assert response.json()[0]["_bulk_download_path"] == path
    assert response.json()[0]["_related_biosample_ids"] == ["nmdc:bsm-1"]
    assert "_bulk_download_filename" not in response.json()[0]


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
