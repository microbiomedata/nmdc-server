"""Tests for env triad validation logic and API endpoints."""

import pytest
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from nmdc_server import fakes
from nmdc_server.env_triad import (
    parse_ontology_id,
    validate_sample_data_triad,
)
from nmdc_server.ingest import envo


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
    fakes.OntologyClassFactory(id="ENVO:00000001", name="environmental system", is_root=True)
    fakes.OntologyClassFactory(
        id="ENVO:00000428", name="biome", definition="A biome is an ecosystem"
    )
    fakes.OntologyClassFactory(
        id="ENVO:00000446", name="terrestrial biome", definition="A biome that is on land"
    )
    fakes.OntologyClassFactory(
        id="ENVO:01000219",
        name="anthropogenic terrestrial biome",
        definition="A terrestrial biome that has been modified by humans",
    )
    fakes.OntologyClassFactory(id="ENVO:00010483", name="environmental material", is_root=True)
    fakes.OntologyClassFactory(
        id="ENVO:00001998", name="soil", definition="Soil is an environmental material"
    )
    fakes.OntologyClassFactory(id="ENVO:01000813", name="astronomical body part", is_root=True)
    fakes.OntologyClassFactory(
        id="ENVO:00000067", name="cave", definition="A natural underground space"
    )
    fakes.OntologyClassFactory(
        id="ENVO:99999999",
        name="obsolete term",
        is_obsolete=True,
        definition="This term is obsolete",
    )
    # Non-ENVO term (Plant Ontology)
    fakes.OntologyClassFactory(id="PO:0025143", name="tepal apex")
    fakes.OntologyClassFactory(id="PO:0025034", name="leaf")
    # Organism-determined environmental system
    fakes.OntologyClassFactory(
        id="ENVO:01001000",
        name="environmental system determined by an organism",
        is_root=True,
    )
    fakes.OntologyClassFactory(
        id="ENVO:01001001",
        name="plant-associated environment",
        definition="An environmental system determined by a plant",
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

    fakes.OntologyRelationFactory(
        subject="ENVO:01001001", predicate="rdfs:subClassOf", object="ENVO:01001000"
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
    db.commit()  # Commit so endpoint tests (which use a separate session) can see the data


# --- Unit tests for parse_ontology_id ---


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("terrestrial biome [ENVO:00000446]", "ENVO:00000446"),
        ("__terrestrial biome [ENVO:00000446]", "ENVO:00000446"),
        ("tepal apex [PO:0025143]", "PO:0025143"),
        ("skin of eyelid [UBERON:0001457]", "UBERON:0001457"),
        ("just some text", None),
        ("", None),
    ],
)
def test_parse_ontology_id(input_str, expected):
    assert parse_ontology_id(input_str) == expected


# --- Integration tests for validate_sample_data_triad ---


def test_valid_triad_passes_ontology_checks(db: Session, ontology_hierarchy):
    """Valid ontology terms in the correct hierarchy should pass."""
    samples = [
        {
            "samp_name": "Sample 1",
            "env_broad_scale": "terrestrial biome [ENVO:00000446]",
            "env_local_scale": "cave [ENVO:00000067]",
            "env_medium": "soil [ENVO:00001998]",
        },
    ]

    result = validate_sample_data_triad(db, samples, "not-a-confirmed-env", "soil_data")
    assert result == {}


def test_wrong_hierarchy_local_scale_not_astronomical_body_part(db: Session, ontology_hierarchy):
    """env_local_scale must be a subclass of astronomical body part."""
    samples = [
        {
            "samp_name": "Sample 1",
            "env_broad_scale": "terrestrial biome [ENVO:00000446]",
            # soil is environmental material, not astronomical body part
            "env_local_scale": "soil [ENVO:00001998]",
            "env_medium": "soil [ENVO:00001998]",
        },
    ]

    result = validate_sample_data_triad(db, samples, "not-a-confirmed-env", "soil_data")
    assert "not a subclass of astronomical body part" in result[0]["env_local_scale"]


def test_wrong_hierarchy_medium_not_environmental_material(db: Session, ontology_hierarchy):
    """env_medium must be a subclass of environmental material."""
    samples = [
        {
            "samp_name": "Sample 1",
            "env_broad_scale": "terrestrial biome [ENVO:00000446]",
            "env_local_scale": "cave [ENVO:00000067]",
            # cave is astronomical body part, not environmental material
            "env_medium": "cave [ENVO:00000067]",
        },
    ]

    result = validate_sample_data_triad(db, samples, "not-a-confirmed-env", "soil_data")
    assert "not a subclass of environmental material" in result[0]["env_medium"]


def test_unparseable_ontology_id(db: Session, ontology_hierarchy):
    """Values without a [CURIE] should fail validation."""
    samples = [
        {
            "samp_name": "Sample 1",
            "env_broad_scale": "just some text without brackets",
            "env_local_scale": "also no brackets",
            "env_medium": "no brackets here either",
        },
    ]

    result = validate_sample_data_triad(db, samples, "not-a-confirmed-env", "soil_data")
    assert "Could not parse ontology ID" in result[0]["env_broad_scale"]
    assert "Could not parse ontology ID" in result[0]["env_local_scale"]
    assert "Could not parse ontology ID" in result[0]["env_medium"]


def test_term_not_in_database(db: Session, ontology_hierarchy):
    """Terms with valid CURIE format but not in the database should fail."""
    samples = [
        {
            "samp_name": "Sample 1",
            "env_broad_scale": "nonexistent [ENVO:00000000]",
            "env_local_scale": "cave [ENVO:00000067]",
            "env_medium": "soil [ENVO:00001998]",
        },
    ]

    result = validate_sample_data_triad(db, samples, "not-a-confirmed-env", "soil_data")
    assert "ENVO:00000000" in result[0]["env_broad_scale"]
    assert "not found" in result[0]["env_broad_scale"]
    assert result[0].get("env_local_scale") is None  # valid term, no error
    assert result[0].get("env_medium") is None  # valid term, no error


def test_obsolete_term_rejected(db: Session, ontology_hierarchy):
    """Obsolete terms should fail validation."""
    samples = [
        {
            "samp_name": "Sample 1",
            "env_broad_scale": "obsolete term [ENVO:99999999]",
            "env_local_scale": "cave [ENVO:00000067]",
            "env_medium": "soil [ENVO:00001998]",
        },
    ]

    result = validate_sample_data_triad(db, samples, "not-a-confirmed-env", "soil_data")
    assert "obsolete" in result[0]["env_broad_scale"]


def test_wrong_hierarchy_broad_scale_not_biome(db: Session, ontology_hierarchy):
    """env_broad_scale must be a subclass of biome or organism-determined env system."""
    samples = [
        {
            "samp_name": "Sample 1",
            # soil is environmental material, not biome or organism-determined env system
            "env_broad_scale": "soil [ENVO:00001998]",
            "env_local_scale": "cave [ENVO:00000067]",
            "env_medium": "soil [ENVO:00001998]",
        },
    ]

    result = validate_sample_data_triad(db, samples, "not-a-confirmed-env", "soil_data")
    assert "not a subclass of" in result[0]["env_broad_scale"]
    assert "biome" in result[0]["env_broad_scale"]


def test_wrong_hierarchy_medium_is_biome(db: Session, ontology_hierarchy):
    """env_medium should NOT be a subclass of biome."""
    samples = [
        {
            "samp_name": "Sample 1",
            "env_broad_scale": "terrestrial biome [ENVO:00000446]",
            "env_local_scale": "cave [ENVO:00000067]",
            # biome term used as medium - wrong
            "env_medium": "terrestrial biome [ENVO:00000446]",
        },
    ]

    result = validate_sample_data_triad(db, samples, "not-a-confirmed-env", "soil_data")
    assert "should not be a subclass of biome" in result[0]["env_medium"]


def test_duplicate_term_broad_and_local_scale(db: Session, ontology_hierarchy):
    """Same ontology ID in env_broad_scale and env_local_scale should produce error."""
    samples = [
        {
            "samp_name": "Sample 1",
            "env_broad_scale": "terrestrial biome [ENVO:00000446]",
            "env_local_scale": "terrestrial biome [ENVO:00000446]",
            "env_medium": "soil [ENVO:00001998]",
        },
    ]

    result = validate_sample_data_triad(db, samples, "not-a-confirmed-env", "soil_data")
    assert "ENVO:00000446" in result[0]["env_local_scale"]
    assert "env_broad_scale" in result[0]["env_local_scale"]


def test_duplicate_term_local_and_medium(db: Session, ontology_hierarchy):
    """Same ontology ID in env_local_scale and env_medium should produce error."""
    samples = [
        {
            "samp_name": "Sample 1",
            "env_broad_scale": "terrestrial biome [ENVO:00000446]",
            "env_local_scale": "soil [ENVO:00001998]",
            "env_medium": "soil [ENVO:00001998]",
        },
    ]

    result = validate_sample_data_triad(db, samples, "not-a-confirmed-env", "soil_data")
    assert "ENVO:00001998" in result[0]["env_medium"]
    assert "env_local_scale" in result[0]["env_medium"]


def test_duplicate_term_all_three_same(db: Session, ontology_hierarchy):
    """Same ontology ID in all three triad slots should produce errors on local and medium."""
    samples = [
        {
            "samp_name": "Sample 1",
            "env_broad_scale": "terrestrial biome [ENVO:00000446]",
            "env_local_scale": "terrestrial biome [ENVO:00000446]",
            "env_medium": "terrestrial biome [ENVO:00000446]",
        },
    ]

    result = validate_sample_data_triad(db, samples, "not-a-confirmed-env", "soil_data")
    # Duplicate errors on local_scale and medium
    assert "ENVO:00000446" in result[0]["env_local_scale"]
    assert "ENVO:00000446" in result[0]["env_medium"]


def test_po_term_allowed_for_plant_associated_local_scale(db: Session, ontology_hierarchy):
    """PO terms should be allowed for env_local_scale in plant_associated_data."""
    samples = [
        {
            "samp_name": "Plant Sample 1",
            "env_broad_scale": "terrestrial biome [ENVO:00000446]",
            "env_local_scale": "tepal apex [PO:0025143]",
            "env_medium": "soil [ENVO:00001998]",
        },
    ]

    result = validate_sample_data_triad(db, samples, "not-a-confirmed-env", "plant_associated_data")
    assert result.get(0) is None  # PO term allowed for plant_associated local_scale


def test_po_term_allowed_for_plant_associated_env_medium(db: Session, ontology_hierarchy):
    """PO terms should be allowed for env_medium in plant_associated_data."""
    samples = [
        {
            "samp_name": "Plant Sample 1",
            "env_broad_scale": "terrestrial biome [ENVO:00000446]",
            "env_local_scale": "cave [ENVO:00000067]",
            "env_medium": "leaf [PO:0025034]",
        },
    ]

    result = validate_sample_data_triad(db, samples, "not-a-confirmed-env", "plant_associated_data")
    assert result.get(0) is None  # PO term allowed for plant_associated env_medium


def test_po_term_allowed_for_soil_env_medium(db: Session, ontology_hierarchy):
    """PO terms should be allowed for env_medium in soil_data (schema permits PO)."""
    samples = [
        {
            "samp_name": "Soil Sample 1",
            "env_broad_scale": "terrestrial biome [ENVO:00000446]",
            "env_local_scale": "cave [ENVO:00000067]",
            "env_medium": "leaf [PO:0025034]",
        },
    ]

    result = validate_sample_data_triad(db, samples, "not-a-confirmed-env", "soil_data")
    assert result.get(0) is None  # PO term allowed for soil env_medium per schema


def test_po_term_rejected_for_sediment_env_medium(db: Session, ontology_hierarchy):
    """PO terms should NOT be allowed for env_medium in sediment_data (schema restricts to ENVO)."""
    samples = [
        {
            "samp_name": "Sediment Sample 1",
            "env_broad_scale": "terrestrial biome [ENVO:00000446]",
            "env_local_scale": "cave [ENVO:00000067]",
            "env_medium": "leaf [PO:0025034]",
        },
    ]

    result = validate_sample_data_triad(db, samples, "not-a-confirmed-env", "sediment_data")
    assert "not a subclass of" in result[0]["env_medium"]


def test_organism_determined_env_system_allowed_for_broad_scale(db: Session, ontology_hierarchy):
    """Terms that are subclasses of ENVO:01001000 should be allowed for env_broad_scale."""
    samples = [
        {
            "samp_name": "Plant Sample 1",
            "env_broad_scale": "plant-associated environment [ENVO:01001001]",
            "env_local_scale": "cave [ENVO:00000067]",
            "env_medium": "soil [ENVO:00001998]",
        },
    ]

    result = validate_sample_data_triad(
        db, samples, "not-a-confirmed-env", "plant_associated_data"
    )
    assert result.get(0) is None  # organism-determined env system accepted for broad_scale


def test_multiple_samples_mixed_validity(db: Session, ontology_hierarchy):
    """Mix of valid and invalid samples should return errors only for invalid ones."""
    samples = [
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
    ]

    result = validate_sample_data_triad(db, samples, "not-a-confirmed-env", "soil_data")
    assert result.get(0) is None  # first sample has no errors
    assert "Could not parse ontology ID" in result[1]["env_broad_scale"]


def test_empty_samples_list(db: Session, ontology_hierarchy):
    """Empty samples list should return empty result."""
    result = validate_sample_data_triad(db, [], "soil", "soil_data")
    assert result == {}


# --- API endpoint tests ---


def test_validate_env_triad_endpoint(
    db: Session, client: TestClient, logged_in_user, ontology_hierarchy
):
    """POST /metadata_submission/validate_env_triad validates sample data."""
    response = client.post(
        "/api/metadata_submission/validate_env_triad",
        json={
            "samples": [
                {
                    "samp_name": "Sample 1",
                    "env_broad_scale": "terrestrial biome [ENVO:00000446]",
                    "env_local_scale": "cave [ENVO:00000067]",
                    "env_medium": "soil [ENVO:00001998]",
                },
            ],
            "env_package": "not-a-confirmed-env",
            "template_type": "soil_data",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body == {}


def test_validate_env_triad_endpoint_with_errors(
    db: Session, client: TestClient, logged_in_user, ontology_hierarchy
):
    """Endpoint returns field errors keyed by row and field name."""
    response = client.post(
        "/api/metadata_submission/validate_env_triad",
        json={
            "samples": [
                {
                    "samp_name": "Bad Sample",
                    "env_broad_scale": "no brackets",
                    "env_local_scale": "cave [ENVO:00000067]",
                    "env_medium": "obsolete term [ENVO:99999999]",
                },
            ],
            "env_package": "not-a-confirmed-env",
            "template_type": "soil_data",
        },
    )
    assert response.status_code == 200
    body = response.json()
    row_errors = body["0"]  # JSON keys are strings
    assert "Could not parse ontology ID" in row_errors["env_broad_scale"]
    assert "obsolete" in row_errors["env_medium"]
