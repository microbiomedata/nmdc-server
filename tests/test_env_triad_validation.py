"""Tests for env triad validation logic and API endpoints."""

import pytest
from fastapi.encoders import jsonable_encoder
from nmdc_schema.nmdc import SubmissionStatusEnum
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from nmdc_server import fakes, models
from nmdc_server.ingest import envo
from nmdc_server.models import SubmissionEditorRole
from nmdc_server.validation.env_triad import (
    ASTRONOMICAL_BODY_PART,
    BIOME,
    ENVIRONMENTAL_MATERIAL,
    FieldValidationResult,
    parse_ontology_id,
    validate_submission_triad,
)


@pytest.fixture
def ontology_hierarchy(db: Session):
    """Set up a realistic ontology hierarchy in the database.

    Creates:
    - ENVO:00000001 (environmental system) - root
    - ENVO:00000428 (biome) - subclass of environmental system
    - ENVO:00000446 (terrestrial biome) - subclass of biome
    - ENVO:01000219 (anthropogenic terrestrial biome) - subclass of terrestrial biome
    - ENVO:00010483 (environmental material) - root
    - ENVO:00001998 (soil) - subclass of environmental material
    - ENVO:01000813 (astronomical body part) - root
    - ENVO:00000067 (cave) - subclass of astronomical body part
    - ENVO:99999999 (obsolete term) - obsolete
    - PO:0025143 (tepal apex) - plant ontology term (in ontology_class only)
    """
    # Root terms
    fakes.OntologyClassFactory(
        id="ENVO:00000001", name="environmental system", is_root=True
    )
    fakes.OntologyClassFactory(
        id="ENVO:00000428", name="biome",
        definition="A biome is an ecosystem"
    )
    fakes.OntologyClassFactory(
        id="ENVO:00000446", name="terrestrial biome",
        definition="A biome that is on land"
    )
    fakes.OntologyClassFactory(
        id="ENVO:01000219", name="anthropogenic terrestrial biome",
        definition="A terrestrial biome that has been modified by humans"
    )
    fakes.OntologyClassFactory(
        id="ENVO:00010483", name="environmental material", is_root=True
    )
    fakes.OntologyClassFactory(
        id="ENVO:00001998", name="soil",
        definition="Soil is an environmental material"
    )
    fakes.OntologyClassFactory(
        id="ENVO:01000813", name="astronomical body part", is_root=True
    )
    fakes.OntologyClassFactory(
        id="ENVO:00000067", name="cave",
        definition="A natural underground space"
    )
    fakes.OntologyClassFactory(
        id="ENVO:99999999", name="obsolete term",
        is_obsolete=True, definition="This term is obsolete"
    )
    # Non-ENVO term (Plant Ontology)
    fakes.OntologyClassFactory(
        id="PO:0025143", name="tepal apex"
    )
    db.commit()

    # Relationships: rdfs:subClassOf (direct parents)
    fakes.OntologyRelationFactory(
        subject="ENVO:00000428", predicate="rdfs:subClassOf", object="ENVO:00000001"
    )
    fakes.OntologyRelationFactory(
        subject="ENVO:00000446", predicate="rdfs:subClassOf", object="ENVO:00000428"
    )
    fakes.OntologyRelationFactory(
        subject="ENVO:01000219", predicate="rdfs:subClassOf", object="ENVO:00000446"
    )
    fakes.OntologyRelationFactory(
        subject="ENVO:00001998", predicate="rdfs:subClassOf", object="ENVO:00010483"
    )
    fakes.OntologyRelationFactory(
        subject="ENVO:00000067", predicate="rdfs:subClassOf", object="ENVO:01000813"
    )

    # Transitive closure entries
    fakes.OntologyRelationFactory(
        subject="ENVO:00000446", predicate="entailed_isa_partof_closure", object="ENVO:00000001"
    )
    fakes.OntologyRelationFactory(
        subject="ENVO:01000219", predicate="entailed_isa_partof_closure", object="ENVO:00000428"
    )
    fakes.OntologyRelationFactory(
        subject="ENVO:01000219", predicate="entailed_isa_partof_closure", object="ENVO:00000001"
    )
    db.commit()

    # Populate envo_term and envo_ancestor from the ontology tables
    envo.load(db)


def _make_submission_with_samples(
    db: Session, user, sample_data: dict, package_name: str = "soil", **kwargs
):
    """Helper to create a submission with specific sample data and owner role."""
    submission = fakes.MetadataSubmissionFactory(
        author=user,
        author_orcid=user.orcid,
        metadata_submission={
            "sampleData": sample_data,
            "packageName": package_name,
            "multiOmicsForm": {
                "studyNumber": "", "JGIStudyId": "",
                "omicsProcessingTypes": [], "facilities": [],
            },
            "studyForm": {
                "studyName": "", "piName": "", "piEmail": "", "piOrcid": "",
                "linkOutWebpage": [], "description": "", "notes": "",
                "contributors": [], "alternativeNames": [],
                "GOLDStudyId": "", "NCBIBioProjectId": "",
            },
            "templates": [],
            "addressForm": {
                "shipper": {
                    "name": "", "email": "", "phone": "", "line1": "",
                    "line2": "", "city": "", "state": "", "postalCode": "", "country": "",
                },
                "shippingConditions": "", "sample": "", "description": "",
                "experimentalGoals": "", "randomization": "",
                "permitNumber": "", "biosafetyLevel": "", "comments": "",
            },
            "validationState": {
                "studyForm": None, "multiOmicsForm": None,
                "sampleEnvironmentForm": None, "senderShippingInfoForm": None,
                "sampleMetadata": None,
            },
        },
        **kwargs,
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=user.orcid,
        role=SubmissionEditorRole.owner,
    )
    db.commit()
    return submission


# --- Unit tests for parse_ontology_id ---


def test_parse_ontology_id_standard():
    assert parse_ontology_id("terrestrial biome [ENVO:00000446]") == "ENVO:00000446"


def test_parse_ontology_id_with_leading_underscores():
    assert parse_ontology_id("__terrestrial biome [ENVO:00000446]") == "ENVO:00000446"


def test_parse_ontology_id_no_brackets():
    assert parse_ontology_id("just some text") is None


def test_parse_ontology_id_empty():
    assert parse_ontology_id("") is None


def test_parse_ontology_id_plant_ontology():
    assert parse_ontology_id("tepal apex [PO:0025143]") == "PO:0025143"


def test_parse_ontology_id_uberon():
    assert parse_ontology_id("skin of eyelid [UBERON:0001457]") == "UBERON:0001457"


# --- Integration tests for validate_submission_triad ---


def test_valid_triad_passes_ontology_checks(db: Session, ontology_hierarchy, logged_in_user):
    """A submission with valid ontology terms in the correct hierarchy should pass."""
    submission = _make_submission_with_samples(
        db, logged_in_user,
        sample_data={
            "soil_data": [
                {
                    "samp_name": "Sample 1",
                    "env_broad_scale": "terrestrial biome [ENVO:00000446]",
                    "env_local_scale": "cave [ENVO:00000067]",
                    "env_medium": "soil [ENVO:00001998]",
                },
            ],
        },
        package_name="not-a-confirmed-env",  # forces ontology fallback
    )

    result = validate_submission_triad(db, submission)
    assert result.valid is True
    assert result.error_count == 0


def test_missing_required_fields(db: Session, ontology_hierarchy, logged_in_user):
    """Missing env triad fields should produce errors."""
    submission = _make_submission_with_samples(
        db, logged_in_user,
        sample_data={
            "soil_data": [
                {
                    "samp_name": "Sample 1",
                    # All three fields missing
                },
            ],
        },
    )

    result = validate_submission_triad(db, submission)
    assert result.valid is False
    assert result.error_count == 3  # one per missing field


def test_empty_string_fields(db: Session, ontology_hierarchy, logged_in_user):
    """Empty string env triad fields should produce errors."""
    submission = _make_submission_with_samples(
        db, logged_in_user,
        sample_data={
            "soil_data": [
                {
                    "samp_name": "Sample 1",
                    "env_broad_scale": "",
                    "env_local_scale": "  ",
                    "env_medium": "",
                },
            ],
        },
    )

    result = validate_submission_triad(db, submission)
    assert result.valid is False
    assert result.error_count == 3


def test_unparseable_ontology_id(db: Session, ontology_hierarchy, logged_in_user):
    """Values without a [CURIE] should fail validation."""
    submission = _make_submission_with_samples(
        db, logged_in_user,
        sample_data={
            "soil_data": [
                {
                    "samp_name": "Sample 1",
                    "env_broad_scale": "just some text without brackets",
                    "env_local_scale": "also no brackets",
                    "env_medium": "no brackets here either",
                },
            ],
        },
        package_name="not-a-confirmed-env",
    )

    result = validate_submission_triad(db, submission)
    assert result.valid is False
    assert result.error_count == 3
    sample = result.sample_results["soil_data"][0]
    assert "Could not parse ontology ID" in sample.env_broad_scale.errors[0]


def test_term_not_in_database(db: Session, ontology_hierarchy, logged_in_user):
    """Terms with valid CURIE format but not in the database should fail."""
    submission = _make_submission_with_samples(
        db, logged_in_user,
        sample_data={
            "soil_data": [
                {
                    "samp_name": "Sample 1",
                    "env_broad_scale": "nonexistent [ENVO:00000000]",
                    "env_local_scale": "cave [ENVO:00000067]",
                    "env_medium": "soil [ENVO:00001998]",
                },
            ],
        },
        package_name="not-a-confirmed-env",
    )

    result = validate_submission_triad(db, submission)
    assert result.valid is False
    sample = result.sample_results["soil_data"][0]
    assert "not found" in sample.env_broad_scale.errors[0]
    assert sample.env_local_scale.valid is True
    assert sample.env_medium.valid is True


def test_obsolete_term_rejected(db: Session, ontology_hierarchy, logged_in_user):
    """Obsolete terms should fail validation."""
    submission = _make_submission_with_samples(
        db, logged_in_user,
        sample_data={
            "soil_data": [
                {
                    "samp_name": "Sample 1",
                    "env_broad_scale": "obsolete term [ENVO:99999999]",
                    "env_local_scale": "cave [ENVO:00000067]",
                    "env_medium": "soil [ENVO:00001998]",
                },
            ],
        },
        package_name="not-a-confirmed-env",
    )

    result = validate_submission_triad(db, submission)
    assert result.valid is False
    sample = result.sample_results["soil_data"][0]
    assert "obsolete" in sample.env_broad_scale.errors[0]


def test_wrong_hierarchy_broad_scale_not_biome(db: Session, ontology_hierarchy, logged_in_user):
    """env_broad_scale must be a subclass of biome."""
    submission = _make_submission_with_samples(
        db, logged_in_user,
        sample_data={
            "soil_data": [
                {
                    "samp_name": "Sample 1",
                    # soil is environmental material, not biome
                    "env_broad_scale": "soil [ENVO:00001998]",
                    "env_local_scale": "cave [ENVO:00000067]",
                    "env_medium": "soil [ENVO:00001998]",
                },
            ],
        },
        package_name="not-a-confirmed-env",
    )

    result = validate_submission_triad(db, submission)
    assert result.valid is False
    sample = result.sample_results["soil_data"][0]
    assert "not a subclass of biome" in sample.env_broad_scale.errors[0]


def test_wrong_hierarchy_medium_is_biome(db: Session, ontology_hierarchy, logged_in_user):
    """env_medium should NOT be a subclass of biome."""
    submission = _make_submission_with_samples(
        db, logged_in_user,
        sample_data={
            "soil_data": [
                {
                    "samp_name": "Sample 1",
                    "env_broad_scale": "terrestrial biome [ENVO:00000446]",
                    "env_local_scale": "cave [ENVO:00000067]",
                    # biome term used as medium - wrong
                    "env_medium": "terrestrial biome [ENVO:00000446]",
                },
            ],
        },
        package_name="not-a-confirmed-env",
    )

    result = validate_submission_triad(db, submission)
    assert result.valid is False
    sample = result.sample_results["soil_data"][0]
    assert any("should not be a subclass of biome" in e for e in sample.env_medium.errors)


def test_duplicate_term_across_triad_slots(db: Session, ontology_hierarchy, logged_in_user):
    """Same ontology ID used in multiple triad slots should produce cross-field error."""
    submission = _make_submission_with_samples(
        db, logged_in_user,
        sample_data={
            "soil_data": [
                {
                    "samp_name": "Sample 1",
                    "env_broad_scale": "terrestrial biome [ENVO:00000446]",
                    "env_local_scale": "terrestrial biome [ENVO:00000446]",
                    "env_medium": "soil [ENVO:00001998]",
                },
            ],
        },
        package_name="not-a-confirmed-env",
    )

    result = validate_submission_triad(db, submission)
    sample = result.sample_results["soil_data"][0]
    assert len(sample.cross_field_errors) > 0
    assert "ENVO:00000446" in sample.cross_field_errors[0]


def test_po_term_allowed_for_plant_associated_local_scale(
    db: Session, ontology_hierarchy, logged_in_user
):
    """PO terms should be allowed for env_local_scale in plant_associated_data."""
    submission = _make_submission_with_samples(
        db, logged_in_user,
        sample_data={
            "plant_associated_data": [
                {
                    "samp_name": "Plant Sample 1",
                    "env_broad_scale": "terrestrial biome [ENVO:00000446]",
                    "env_local_scale": "tepal apex [PO:0025143]",
                    "env_medium": "soil [ENVO:00001998]",
                },
            ],
        },
        package_name="not-a-confirmed-env",
    )

    result = validate_submission_triad(db, submission)
    sample = result.sample_results["plant_associated_data"][0]
    # PO term should not produce hierarchy errors for local_scale
    assert sample.env_local_scale.valid is True


def test_multiple_samples_mixed_validity(db: Session, ontology_hierarchy, logged_in_user):
    """Submission with mix of valid and invalid samples should fail overall."""
    submission = _make_submission_with_samples(
        db, logged_in_user,
        sample_data={
            "soil_data": [
                {
                    "samp_name": "Good Sample",
                    "env_broad_scale": "terrestrial biome [ENVO:00000446]",
                    "env_local_scale": "cave [ENVO:00000067]",
                    "env_medium": "soil [ENVO:00001998]",
                },
                {
                    "samp_name": "Bad Sample",
                    "env_broad_scale": "no brackets here",
                    "env_local_scale": "cave [ENVO:00000067]",
                    "env_medium": "soil [ENVO:00001998]",
                },
            ],
        },
        package_name="not-a-confirmed-env",
    )

    result = validate_submission_triad(db, submission)
    assert result.valid is False
    assert result.error_count >= 1
    samples = result.sample_results["soil_data"]
    assert samples[0].env_broad_scale.valid is True
    assert samples[1].env_broad_scale.valid is False


def test_non_environmental_data_slots_ignored(db: Session, ontology_hierarchy, logged_in_user):
    """Sample data under non-ENVIRONMENTAL_DATA_SLOTS keys should be ignored."""
    submission = _make_submission_with_samples(
        db, logged_in_user,
        sample_data={
            "jgi_mg_data": [
                {
                    "samp_name": "JGI Sample",
                    # No env triad fields, but this isn't an environmental slot
                },
            ],
        },
        package_name="not-a-confirmed-env",
    )

    result = validate_submission_triad(db, submission)
    assert result.valid is True
    assert "jgi_mg_data" not in result.sample_results


def test_submission_with_no_sample_data(db: Session, ontology_hierarchy, logged_in_user):
    """Submission with empty sampleData should pass (no samples to validate)."""
    submission = _make_submission_with_samples(
        db, logged_in_user,
        sample_data={},
    )

    result = validate_submission_triad(db, submission)
    assert result.valid is True
    assert result.error_count == 0


# --- API endpoint tests ---


def test_validate_env_triad_single_endpoint(
    db: Session, client: TestClient, logged_in_user, ontology_hierarchy
):
    """POST /metadata_submission/{id}/validate_env_triad returns validation results."""
    submission = _make_submission_with_samples(
        db, logged_in_user,
        sample_data={
            "soil_data": [
                {
                    "samp_name": "Sample 1",
                    "env_broad_scale": "terrestrial biome [ENVO:00000446]",
                    "env_local_scale": "cave [ENVO:00000067]",
                    "env_medium": "soil [ENVO:00001998]",
                },
            ],
        },
        package_name="not-a-confirmed-env",
    )

    response = client.post(f"/api/metadata_submission/{submission.id}/validate_env_triad")
    assert response.status_code == 200
    body = response.json()
    assert body["submission_id"] == str(submission.id)
    assert body["valid"] is True
    assert body["error_count"] == 0


def test_validate_env_triad_single_endpoint_with_errors(
    db: Session, client: TestClient, logged_in_user, ontology_hierarchy
):
    """Endpoint returns structured errors for invalid submissions."""
    submission = _make_submission_with_samples(
        db, logged_in_user,
        sample_data={
            "soil_data": [
                {
                    "samp_name": "Bad Sample",
                    "env_broad_scale": "no brackets",
                    "env_local_scale": "",
                    "env_medium": "obsolete term [ENVO:99999999]",
                },
            ],
        },
        package_name="not-a-confirmed-env",
    )

    response = client.post(f"/api/metadata_submission/{submission.id}/validate_env_triad")
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert body["error_count"] >= 3

    soil_sample = body["sample_results"]["soil_data"][0]
    assert soil_sample["env_broad_scale"]["valid"] is False
    assert soil_sample["env_local_scale"]["valid"] is False
    assert soil_sample["env_medium"]["valid"] is False


def test_validate_env_triad_bulk_endpoint_requires_admin(
    db: Session, client: TestClient, logged_in_user
):
    """GET /metadata_submission/validate_env_triad requires admin."""
    response = client.get("/api/metadata_submission/validate_env_triad")
    assert response.status_code == 403


def test_validate_env_triad_bulk_endpoint(
    db: Session, client: TestClient, logged_in_admin_user, ontology_hierarchy
):
    """Admin bulk validation returns results for matching submissions."""
    _make_submission_with_samples(
        db, logged_in_admin_user,
        sample_data={
            "soil_data": [
                {
                    "samp_name": "Sample 1",
                    "env_broad_scale": "terrestrial biome [ENVO:00000446]",
                    "env_local_scale": "cave [ENVO:00000067]",
                    "env_medium": "soil [ENVO:00001998]",
                },
            ],
        },
        package_name="not-a-confirmed-env",
        status=SubmissionStatusEnum.SubmittedPendingReview.text,
    )

    response = client.get("/api/metadata_submission/validate_env_triad")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["valid"] is True


# --- Status change gate tests ---


def test_status_change_blocked_for_invalid_triad(
    db: Session, client: TestClient, logged_in_user, ontology_hierarchy
):
    """Transitioning to SubmittedPendingReview should fail with invalid env triad."""
    submission = _make_submission_with_samples(
        db, logged_in_user,
        sample_data={
            "soil_data": [
                {
                    "samp_name": "Bad Sample",
                    "env_broad_scale": "no brackets at all",
                    "env_local_scale": "cave [ENVO:00000067]",
                    "env_medium": "soil [ENVO:00001998]",
                },
            ],
        },
        package_name="not-a-confirmed-env",
        status=SubmissionStatusEnum.InProgress.text,
    )

    response = client.request(
        method="patch",
        url=f"/api/metadata_submission/{submission.id}/status",
        json=jsonable_encoder({"status": SubmissionStatusEnum.SubmittedPendingReview.text}),
    )
    assert response.status_code == 422
    body = response.json()
    assert "env triad validation errors" in body["detail"]["message"]


def test_status_change_allowed_for_valid_triad(
    db: Session, client: TestClient, logged_in_user, ontology_hierarchy
):
    """Transitioning to SubmittedPendingReview should succeed with valid env triad."""
    submission = _make_submission_with_samples(
        db, logged_in_user,
        sample_data={
            "soil_data": [
                {
                    "samp_name": "Good Sample",
                    "env_broad_scale": "terrestrial biome [ENVO:00000446]",
                    "env_local_scale": "cave [ENVO:00000067]",
                    "env_medium": "soil [ENVO:00001998]",
                },
            ],
        },
        package_name=["not-a-confirmed-env"],
        status=SubmissionStatusEnum.InProgress.text,
        is_test_submission=True,  # avoid GitHub issue creation
    )

    response = client.request(
        method="patch",
        url=f"/api/metadata_submission/{submission.id}/status",
        json=jsonable_encoder({"status": SubmissionStatusEnum.SubmittedPendingReview.text}),
    )
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
    assert response.json()["status"] == SubmissionStatusEnum.SubmittedPendingReview.text
