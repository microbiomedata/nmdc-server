from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from nmdc_schema.nmdc import SubmissionStatusEnum
from sqlalchemy.orm import Session

from nmdc_server import lims_export, models
from nmdc_server.config import settings
from nmdc_server.models import SubmissionEditorRole
from tests import fakes


def _sample_set(**overrides) -> models.SubmissionSampleSet:
    """A minimal SubmissionSampleSet object (no DB) for build_lims_payloads unit tests."""
    defaults = dict(
        id=uuid4(),
        submission_metadata_id=uuid4(),
        name="Sample Set",
        status=SubmissionStatusEnum.ApprovedHeld.text,
        templates=[],
        sample_environment_form={},
        sender_shipping_info_form={},
        multi_omics_form={"studyNumber": "61258"},
        sample_data={"data": {}},
    )
    defaults.update(overrides)
    return models.SubmissionSampleSet(**defaults)


# --------------------------------------------------------------------------- build_lims_payloads


def test_build_payloads_env_slot_and_companion_merge(monkeypatch):
    monkeypatch.setattr(lims_export, "_resolve_project_uuid", lambda pid: "resolved-uuid")
    ss = _sample_set(
        sample_data={
            "data": {
                "soil_data": [{"samp_name": "S1", "env_medium": "soil [ENVO:1]"}],
                # companion tab: merged by samp_name, NOT sent as its own sample
                "emsl_data": [{"samp_name": "S1", "analysis_type": ["metagenomics"]}],
            }
        }
    )
    payloads = lims_export.build_lims_payloads(ss)

    assert len(payloads) == 1  # only the soil sample, emsl_data merged in
    p = payloads[0]
    assert p["sample_type"] == "soil"
    assert p["project_id"] == "61258"
    assert p["project_uuid"] == "resolved-uuid"
    assert p["shipment_tracking_number"] == ""  # left off, not synthesized
    # samp_name -> sample_name; companion analysis_type merged onto the sample
    assert p["sample_data"]["sample_name"] == "S1"
    assert "samp_name" not in p["sample_data"]
    assert p["sample_data"]["analysis_type"] == ["metagenomics"]


def test_build_payloads_skips_unmapped_slot(monkeypatch):
    monkeypatch.setattr(lims_export, "_resolve_project_uuid", lambda pid: "u")
    # host_associated_data has no ESP sample-type mapping -> skipped (no bogus sample)
    ss = _sample_set(sample_data={"data": {"host_associated_data": [{"samp_name": "H1"}]}})
    assert lims_export.build_lims_payloads(ss) == []


def test_build_payloads_skips_when_not_emsl_bound(monkeypatch):
    monkeypatch.setattr(lims_export, "_resolve_project_uuid", lambda pid: "u")
    # no 5-digit EMSL proposal number -> not EMSL-bound -> nothing exported
    ss = _sample_set(
        multi_omics_form={},
        sample_data={"data": {"soil_data": [{"samp_name": "S1"}]}},
    )
    assert lims_export.build_lims_payloads(ss) == []


def test_resolve_project_uuid_aborts_instead_of_synthesizing(monkeypatch):
    class _FakeDir:
        def get_project_uuid(self, pid):
            return None

    monkeypatch.setattr(lims_export, "get_project_directory", lambda: _FakeDir())
    # Real backend that can't resolve -> abort (do not fabricate a UUID).
    monkeypatch.setattr(settings, "project_directory_backend", "nexus")
    with pytest.raises(lims_export.LimsExportError):
        lims_export._resolve_project_uuid("61258")
    # Offline synthesize backend deliberately returns a deterministic placeholder.
    monkeypatch.setattr(settings, "project_directory_backend", "synthesize")
    assert lims_export._resolve_project_uuid("61258")


def test_slot_to_sample_type_known_and_unknown():
    assert lims_export.slot_to_sample_type("soil_data") == "soil"
    assert lims_export.slot_to_sample_type("misc_envs_data") == "misc-envs"
    assert lims_export.slot_to_sample_type("host_associated_data") is None


# --------------------------------------------------------------------------- endpoint


def _owned_sample_set(
    db,
    user,
    *,
    status=SubmissionStatusEnum.ApprovedHeld.text,
    templates=("emsl",),
    is_test_submission=False,
):
    submission = fakes.SubmissionMetadataFactory(
        author=user, author_orcid=user.orcid, is_test_submission=is_test_submission
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=user.orcid,
        role=SubmissionEditorRole.owner,
    )
    sample_set = fakes.SubmissionSampleSetFactory(
        submission_metadata_id=submission.id, status=status, templates=list(templates)
    )
    db.commit()
    return sample_set


@pytest.fixture(autouse=True)
def _configured(monkeypatch):
    # Ensure the endpoint sees a configured, enabled export for the happy-path tests.
    monkeypatch.setattr(settings, "lims_export_enabled", True)
    monkeypatch.setattr(settings, "lims_gateway_url", "http://lims.test/lims")
    monkeypatch.setattr(settings, "lims_esp_token", "test-token")


def test_send_to_lims_happy_path(db: Session, client: TestClient, logged_in_user, monkeypatch):
    sample_set = _owned_sample_set(db, logged_in_user)
    summary = {"total": 1, "sent": 1, "failed": 0, "results": []}
    monkeypatch.setattr(lims_export, "send_sample_set_to_lims", lambda ss: summary)

    resp = client.post(f"/api/metadata_submission/sample_set/{sample_set.id}/send-to-lims")

    assert resp.status_code == 200
    assert resp.json()["sent"] == 1
    refreshed = db.get(models.SubmissionSampleSet, sample_set.id)
    assert refreshed.lims_export_results == summary
    assert refreshed.lims_exported_at is not None


def test_send_to_lims_wrong_status_409(
    db: Session, client: TestClient, logged_in_user, monkeypatch
):
    sample_set = _owned_sample_set(db, logged_in_user, status=SubmissionStatusEnum.InProgress.text)
    monkeypatch.setattr(lims_export, "send_sample_set_to_lims", lambda ss: {})
    resp = client.post(f"/api/metadata_submission/sample_set/{sample_set.id}/send-to-lims")
    assert resp.status_code == 409


def test_send_to_lims_disabled_503(db: Session, client: TestClient, logged_in_user, monkeypatch):
    sample_set = _owned_sample_set(db, logged_in_user)
    monkeypatch.setattr(settings, "lims_export_enabled", False)
    resp = client.post(f"/api/metadata_submission/sample_set/{sample_set.id}/send-to-lims")
    assert resp.status_code == 503


def test_send_to_lims_unconfigured_503(
    db: Session, client: TestClient, logged_in_user, monkeypatch
):
    sample_set = _owned_sample_set(db, logged_in_user)
    monkeypatch.setattr(settings, "lims_esp_token", "")
    resp = client.post(f"/api/metadata_submission/sample_set/{sample_set.id}/send-to-lims")
    assert resp.status_code == 503


def test_send_to_lims_not_emsl_bound_409(
    db: Session, client: TestClient, logged_in_user, monkeypatch
):
    # ApprovedHeld but no `emsl` template -> not EMSL-bound.
    sample_set = _owned_sample_set(db, logged_in_user, templates=("soil",))
    monkeypatch.setattr(lims_export, "send_sample_set_to_lims", lambda ss: {})
    resp = client.post(f"/api/metadata_submission/sample_set/{sample_set.id}/send-to-lims")
    assert resp.status_code == 409


def test_send_to_lims_test_submission_409(
    db: Session, client: TestClient, logged_in_user, monkeypatch
):
    sample_set = _owned_sample_set(db, logged_in_user, is_test_submission=True)
    monkeypatch.setattr(lims_export, "send_sample_set_to_lims", lambda ss: {})
    resp = client.post(f"/api/metadata_submission/sample_set/{sample_set.id}/send-to-lims")
    assert resp.status_code == 409


def test_send_to_lims_forbidden_for_non_member(
    db: Session, client: TestClient, logged_in_user, monkeypatch
):
    monkeypatch.setattr(lims_export, "send_sample_set_to_lims", lambda ss: {})
    # Sample set on a submission the logged-in user has no role on.
    other = fakes.SubmissionMetadataFactory()
    sample_set = fakes.SubmissionSampleSetFactory(
        submission_metadata_id=other.id, status=SubmissionStatusEnum.ApprovedHeld.text
    )
    db.commit()
    resp = client.post(f"/api/metadata_submission/sample_set/{sample_set.id}/send-to-lims")
    assert resp.status_code in (403, 404)
