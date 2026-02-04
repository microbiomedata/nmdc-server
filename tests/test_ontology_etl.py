"""Test the generic ontology ETL functionality."""

from sqlalchemy.orm import Session

from nmdc_server import fakes, models
from nmdc_server.ingest import envo, ontology


def test_populate_envo_from_generic_ontology(db: Session):
    # Create a 3-level hierarchy: grandparent -> parent -> child
    fakes.OntologyClassFactory(
        id="ENVO:00000001",
        name="environmental system",
        is_root=True,
        definition="The root environmental system",
        alternative_names=["env", "environment"],
        annotations={"test": "data"},
    )
    fakes.OntologyClassFactory(
        id="ENVO:00000428",
        name="biome",
        definition="A biome is an environmental system",
        alternative_names=["ecological biome"],
    )
    fakes.OntologyClassFactory(
        id="ENVO:00000446",
        name="terrestrial biome",
        definition="A biome that is on land",
        alternative_names=["land biome"],
    )
    # Non-ENVO term that should be ignored
    fakes.OntologyClassFactory(id="UBERON:0000001", name="anatomical structure", is_root=True)
    db.commit()

    assert db.query(models.OntologyClass).count() == 4

    # Create relationships (direct and closure)
    fakes.OntologyRelationFactory(
        subject="ENVO:00000428", predicate="rdfs:subClassOf", object="ENVO:00000001"
    )
    fakes.OntologyRelationFactory(
        subject="ENVO:00000446", predicate="rdfs:subClassOf", object="ENVO:00000428"
    )
    fakes.OntologyRelationFactory(
        subject="ENVO:00000446", predicate="entailed_isa_partof_closure", object="ENVO:00000428"
    )
    fakes.OntologyRelationFactory(
        subject="ENVO:00000446", predicate="entailed_isa_partof_closure", object="ENVO:00000001"
    )
    db.commit()

    # Run the ENVO population function
    envo.load(db)

    # Verify EnvoTerm table
    envo_terms = db.query(models.EnvoTerm).order_by(models.EnvoTerm.id).all()
    assert len(envo_terms) == 3  # Should only have ENVO terms, not UBERON

    # Check grandparent term
    grandparent_term = envo_terms[0]
    assert grandparent_term.id == "ENVO:00000001"
    assert grandparent_term.label == "environmental system"
    assert grandparent_term.data["definition"] == "The root environmental system"  # type: ignore
    assert grandparent_term.data["is_root"] is True  # type: ignore
    assert grandparent_term.data["alternative_names"] == ["env", "environment"]  # type: ignore
    assert grandparent_term.data["annotations"]["test"] == "data"  # type: ignore

    # Check parent term
    parent_term = envo_terms[1]
    assert parent_term.id == "ENVO:00000428"
    assert parent_term.label == "biome"
    assert parent_term.data["definition"] == "A biome is an environmental system"  # type: ignore

    # Check child term
    child_term = envo_terms[2]
    assert child_term.id == "ENVO:00000446"
    assert child_term.label == "terrestrial biome"
    assert child_term.data["definition"] == "A biome that is on land"  # type: ignore
    assert child_term.data["is_root"] is False  # type: ignore

    # Verify EnvoAncestor table
    # We should have 6 ancestors:
    # Self-referential (required for faceted search):
    # 1. grandparent -> grandparent (direct=False, self-ref)
    # 2. parent -> parent (direct=False, self-ref)
    # 3. child -> child (direct=False, self-ref)
    # Direct parent relationships:
    # 4. parent -> grandparent (direct=True, from rdfs:subClassOf)
    # 5. child -> parent (direct=True, from rdfs:subClassOf)
    # Indirect relationships:
    # 6. child -> grandparent (direct=False, from closure)
    ancestors = (
        db.query(models.EnvoAncestor)
        .order_by(models.EnvoAncestor.id, models.EnvoAncestor.ancestor_id)
        .all()
    )
    assert len(ancestors) == 6

    # Check grandparent -> grandparent (self-ref)
    assert ancestors[0].id == "ENVO:00000001"
    assert ancestors[0].ancestor_id == "ENVO:00000001"
    assert ancestors[0].direct is False  # Self-refs are always direct=False

    # Check parent -> grandparent (direct)
    assert ancestors[1].id == "ENVO:00000428"
    assert ancestors[1].ancestor_id == "ENVO:00000001"
    assert ancestors[1].direct is True

    # Check parent -> parent (self-ref)
    assert ancestors[2].id == "ENVO:00000428"
    assert ancestors[2].ancestor_id == "ENVO:00000428"
    assert ancestors[2].direct is False

    # Check child -> grandparent (indirect via closure)
    assert ancestors[3].id == "ENVO:00000446"
    assert ancestors[3].ancestor_id == "ENVO:00000001"
    assert ancestors[3].direct is False  # ← Key test: indirect via closure!

    # Check child -> parent (direct)
    assert ancestors[4].id == "ENVO:00000446"
    assert ancestors[4].ancestor_id == "ENVO:00000428"
    assert ancestors[4].direct is True

    # Check child -> child (self-ref)
    assert ancestors[5].id == "ENVO:00000446"
    assert ancestors[5].ancestor_id == "ENVO:00000446"
    assert ancestors[5].direct is False

    # Verify relationships work through the model
    # Child should have 1 direct parent and 3 total ancestors (self + parent + grandparent)
    child_direct_parents = [
        a.ancestor_id
        for a in db.query(models.EnvoAncestor).filter_by(id="ENVO:00000446", direct=True).all()
    ]
    assert child_direct_parents == ["ENVO:00000428"]

    child_all_ancestors = [
        a.ancestor_id
        for a in db.query(models.EnvoAncestor)
        .filter_by(id="ENVO:00000446")
        .order_by(models.EnvoAncestor.ancestor_id)
        .all()
    ]
    assert child_all_ancestors == ["ENVO:00000001", "ENVO:00000428", "ENVO:00000446"]


def test_ontology_etl_integration(db: Session):
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

    # Create test ontology classes - 3-level hierarchy
    class_data = [
        {
            "id": "ENVO:00000001",
            "name": "environmental system",
            "type": "nmdc:OntologyClass",
            "definition": "The root environmental system",
            "alternative_names": ["environment"],
            "is_root": True,
            "is_obsolete": False,
        },
        {
            "id": "ENVO:00000428",
            "name": "biome",
            "type": "nmdc:OntologyClass",
            "definition": "A biome is an environmental system",
            "alternative_names": ["ecological biome"],
            "is_root": False,
            "is_obsolete": False,
            # MongoDB documents may include a 'relations' field that the loader
            # removes before inserting (relations are stored in ontology_relation table)
            "relations": [],
        },
        {
            "id": "ENVO:00000446",
            "name": "terrestrial biome",
            "type": "nmdc:OntologyClass",
            "definition": "A terrestrial biome is a biome on land",
            "alternative_names": [],
            "is_root": False,
            "is_obsolete": False,
        },
    ]

    # Create test relations - direct and closure
    relation_data = [
        # Direct: parent -> grandparent
        {
            "subject": "ENVO:00000428",
            "predicate": "rdfs:subClassOf",
            "object": "ENVO:00000001",
            "type": "nmdc:OntologyRelation",
        },
        # Direct: child -> parent
        {
            "subject": "ENVO:00000446",
            "predicate": "rdfs:subClassOf",
            "object": "ENVO:00000428",
            "type": "nmdc:OntologyRelation",
        },
        # Closure: child -> parent (redundant with direct)
        {
            "subject": "ENVO:00000446",
            "predicate": "entailed_isa_partof_closure",
            "object": "ENVO:00000428",
            "type": "nmdc:OntologyRelation",
        },
        # Closure: child -> grandparent (indirect - the value of closure!)
        {
            "subject": "ENVO:00000446",
            "predicate": "entailed_isa_partof_closure",
            "object": "ENVO:00000001",
            "type": "nmdc:OntologyRelation",
        },
    ]

    # Run the ETL (ontology.load populates generic tables, envo.load populates ENVO tables)
    ontology.load(db, MockCursor(class_data), MockCursor(relation_data))  # type: ignore
    db.commit()

    # Verify generic tables were populated
    assert db.query(models.OntologyClass).count() == 3
    assert db.query(models.OntologyRelation).count() == 4  # 2 direct + 2 closure

    # Now populate ENVO tables from the generic tables
    envo.load(db)

    # Verify the 'relations' field in source data was properly removed by the loader
    # (the biome class had relations: [] in its source document)
    biome_class = db.query(models.OntologyClass).filter_by(id="ENVO:00000428").first()
    assert biome_class is not None
    assert biome_class.name == "biome"
    # The 'relations' field should NOT end up in annotations (it's removed before extract_extras)
    assert "relations" not in (biome_class.annotations or {})

    # Verify ENVO tables were populated
    assert db.query(models.EnvoTerm).count() == 3
    # Should have 6 ancestors:
    # Self-referential (3 terms -> 3 self-refs):
    # 1. grandparent -> grandparent, 2. parent -> parent, 3. child -> child
    # Direct relationships (2):
    # 4. parent -> grandparent, 5. child -> parent
    # Indirect via closure (1):
    # 6. child -> grandparent
    assert db.query(models.EnvoAncestor).count() == 6

    # Check specific term
    biome = db.query(models.EnvoTerm).filter_by(id="ENVO:00000428").first()
    assert biome is not None
    assert biome.label == "biome"
    assert biome.data["definition"] == "A biome is an environmental system"  # type: ignore

    # Verify the closure relationship created an indirect ancestor
    child_to_grandparent = (
        db.query(models.EnvoAncestor)
        .filter_by(id="ENVO:00000446", ancestor_id="ENVO:00000001")
        .first()
    )
    assert child_to_grandparent is not None
    assert child_to_grandparent.direct is False  # ← Key assertion: indirect via closure!


def test_envo_load_with_biosample_fk_constraint(db: Session):
    """Test that envo.load() doesn't violate FK constraints when biosamples reference ENVO terms.

    This verifies the upsert strategy in envo.load() correctly preserves EnvoTerm rows
    that are referenced by biosample.env_* foreign keys.
    """
    # Create ENVO ontology classes
    fakes.OntologyClassFactory(
        id="ENVO:00000001",
        name="environmental system",
        is_root=True,
    )
    fakes.OntologyClassFactory(
        id="ENVO:00000428",
        name="biome",
    )
    fakes.OntologyClassFactory(
        id="ENVO:00000446",
        name="terrestrial biome",
    )
    # Create relationships
    fakes.OntologyRelationFactory(
        subject="ENVO:00000428", predicate="rdfs:subClassOf", object="ENVO:00000001"
    )
    fakes.OntologyRelationFactory(
        subject="ENVO:00000446", predicate="rdfs:subClassOf", object="ENVO:00000428"
    )
    db.commit()

    # First load: populate EnvoTerm table
    envo.load(db)
    db.commit()

    assert db.query(models.EnvoTerm).count() == 3

    # Create EnvoTerm objects for the BiosampleFactory to use
    envo_term_broad = db.query(models.EnvoTerm).filter_by(id="ENVO:00000001").first()
    envo_term_local = db.query(models.EnvoTerm).filter_by(id="ENVO:00000428").first()
    envo_term_medium = db.query(models.EnvoTerm).filter_by(id="ENVO:00000446").first()

    # Create a biosample that references the ENVO terms (creates FK constraints)
    biosample = fakes.BiosampleFactory(
        env_broad_scale=envo_term_broad,
        env_local_scale=envo_term_local,
        env_medium=envo_term_medium,
    )
    db.commit()

    # Verify biosample references the ENVO terms
    assert biosample.env_broad_scale_id == "ENVO:00000001"
    assert biosample.env_local_scale_id == "ENVO:00000428"
    assert biosample.env_medium_id == "ENVO:00000446"

    # Second load: should NOT fail due to FK constraints
    # The upsert strategy in envo.load() should preserve the EnvoTerm rows
    envo.load(db)
    db.commit()

    # Verify ENVO terms still exist and biosample FK references are intact
    assert db.query(models.EnvoTerm).count() == 3
    db.refresh(biosample)
    assert biosample.env_broad_scale_id == "ENVO:00000001"
    assert biosample.env_local_scale.label == "environmental system"
