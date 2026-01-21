"""Test the generic ontology ETL functionality."""

from sqlalchemy.orm import Session

from nmdc_server import models
from nmdc_server.ingest import ontology


def test_populate_envo_from_generic_ontology(db: Session):
    """Test that EnvoTerm and EnvoAncestor are populated correctly from generic ontology tables."""

    # Insert test data into generic ontology tables
    # Create some ENVO terms
    envo_root = models.OntologyClass(
        id="ENVO:00000001",
        name="environment",
        type="nmdc:OntologyClass",
        is_root=True,
        is_obsolete=False,
        definition="The root environment term",
        alternative_names=["env", "environmental system"],
        annotations={"test": "data"},
    )

    envo_child = models.OntologyClass(
        id="ENVO:00000002",
        name="aquatic environment",
        type="nmdc:OntologyClass",
        is_root=False,
        is_obsolete=False,
        definition="An aquatic environment",
        alternative_names=["water environment"],
    )

    # Create a non-ENVO term that should be ignored
    uberon_term = models.OntologyClass(
        id="UBERON:0000001",
        name="anatomical structure",
        type="nmdc:OntologyClass",
        is_root=True,
        is_obsolete=False,
    )

    db.add_all([envo_root, envo_child, uberon_term])

    # Create relationships
    direct_relation = models.OntologyRelation(
        subject="ENVO:00000002",
        predicate="rdfs:subClassOf",
        object="ENVO:00000001",
        type="nmdc:OntologyRelation",
    )

    closure_relation = models.OntologyRelation(
        subject="ENVO:00000002",
        predicate="entailed_isa_partof_closure",
        object="ENVO:00000001",
        type="nmdc:OntologyRelation",
    )

    db.add_all([direct_relation, closure_relation])
    db.commit()

    # Run the population function
    ontology.populate_envo_terms_from_ontology(db)

    # Verify EnvoTerm table
    envo_terms = db.query(models.EnvoTerm).order_by(models.EnvoTerm.id).all()
    assert len(envo_terms) == 2  # Should only have ENVO terms, not UBERON

    # Check root term
    root_term = envo_terms[0]
    assert root_term.id == "ENVO:00000001"
    assert root_term.label == "environment"
    assert root_term.data["definition"] == "The root environment term"  # type: ignore
    assert root_term.data["is_root"] is True  # type: ignore
    assert root_term.data["alternative_names"] == ["env", "environmental system"]  # type: ignore
    assert root_term.data["annotations"]["test"] == "data"  # type: ignore

    # Check child term
    child_term = envo_terms[1]
    assert child_term.id == "ENVO:00000002"
    assert child_term.label == "aquatic environment"
    assert child_term.data["definition"] == "An aquatic environment"  # type: ignore
    assert child_term.data["is_root"] is False  # type: ignore

    # Verify EnvoAncestor table
    ancestors = db.query(models.EnvoAncestor).all()
    assert len(ancestors) == 2  # One direct, one from closure

    # Check direct parent relationship
    direct_ancestor = (
        db.query(models.EnvoAncestor)
        .filter_by(id="ENVO:00000002", ancestor_id="ENVO:00000001", direct=True)
        .first()
    )
    assert direct_ancestor is not None

    # Check closure relationship
    closure_ancestor = (
        db.query(models.EnvoAncestor)
        .filter_by(id="ENVO:00000002", ancestor_id="ENVO:00000001", direct=False)
        .first()
    )
    assert closure_ancestor is not None

    # Verify relationships work through the model
    assert child_term.parent_entities[0].id == "ENVO:00000001"
    assert child_term.ancestor_entities[0].id == "ENVO:00000001"


def test_ontology_etl_integration(db: Session):
    """Test the complete ontology ETL process."""

    # Mock MongoDB cursor data
    class MockCursor:
        def __init__(self, data):
            self.data = data
            self.index = 0

        def __iter__(self):
            return self

        def __next__(self):
            if self.index >= len(self.data):
                raise StopIteration
            item = self.data[self.index]
            self.index += 1
            return item

    # Create test ontology classes
    class_data = [
        {
            "id": "ENVO:00000428",
            "name": "biome",
            "type": "nmdc:OntologyClass",
            "definition": "A biome is...",
            "alternative_names": ["ecological biome"],
            "is_root": False,
            "is_obsolete": False,
            "relations": [],  # Will be removed by loader
        },
        {
            "id": "ENVO:00000446",
            "name": "terrestrial biome",
            "type": "nmdc:OntologyClass",
            "definition": "A terrestrial biome is...",
            "alternative_names": [],
            "is_root": False,
            "is_obsolete": False,
        },
    ]

    # Create test relations
    relation_data = [
        {
            "subject": "ENVO:00000446",
            "predicate": "rdfs:subClassOf",
            "object": "ENVO:00000428",
            "type": "nmdc:OntologyRelation",
        }
    ]

    # Run the ETL
    ontology.load(db, MockCursor(class_data), MockCursor(relation_data))  # type: ignore

    # Verify generic tables were populated
    assert db.query(models.OntologyClass).count() == 2
    assert db.query(models.OntologyRelation).count() == 1

    # Verify ENVO tables were populated
    assert db.query(models.EnvoTerm).count() == 2
    assert db.query(models.EnvoAncestor).count() == 1

    # Check specific term
    biome = db.query(models.EnvoTerm).filter_by(id="ENVO:00000428").first()
    assert biome is not None
    assert biome.label == "biome"
    assert biome.data["definition"] == "A biome is..."  # type: ignore
