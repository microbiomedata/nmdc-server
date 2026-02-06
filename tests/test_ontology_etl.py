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
    # Non-ENVO term - now included to preserve full hierarchy for cross-ontology relationships
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

    # Verify EnvoTerm table - ALL terms are loaded to preserve full hierarchy
    envo_terms = db.query(models.EnvoTerm).order_by(models.EnvoTerm.id).all()
    assert len(envo_terms) == 4  # All terms including UBERON

    # Check grandparent term (ENVO terms are first alphabetically by ID)
    grandparent_term = db.query(models.EnvoTerm).filter_by(id="ENVO:00000001").first()
    assert grandparent_term.id == "ENVO:00000001"
    assert grandparent_term.label == "environmental system"
    assert grandparent_term.data["definition"] == "The root environmental system"  # type: ignore
    assert grandparent_term.data["is_root"] is True  # type: ignore
    assert grandparent_term.data["alternative_names"] == ["env", "environment"]  # type: ignore
    assert grandparent_term.data["annotations"]["test"] == "data"  # type: ignore

    # Check parent term
    parent_term = db.query(models.EnvoTerm).filter_by(id="ENVO:00000428").first()
    assert parent_term.id == "ENVO:00000428"
    assert parent_term.label == "biome"
    assert parent_term.data["definition"] == "A biome is an environmental system"  # type: ignore

    # Check child term
    child_term = db.query(models.EnvoTerm).filter_by(id="ENVO:00000446").first()
    assert child_term.id == "ENVO:00000446"
    assert child_term.label == "terrestrial biome"
    assert child_term.data["definition"] == "A biome that is on land"  # type: ignore
    assert child_term.data["is_root"] is False  # type: ignore

    # Verify EnvoAncestor table
    # We should have 7 ancestors (4 terms = 4 self-refs + 2 direct + 1 indirect):
    # Self-referential (required for faceted search):
    # 1. grandparent -> grandparent (direct=False, self-ref)
    # 2. parent -> parent (direct=False, self-ref)
    # 3. child -> child (direct=False, self-ref)
    # 4. UBERON -> UBERON (direct=False, self-ref)
    # Direct parent relationships:
    # 5. parent -> grandparent (direct=True, from rdfs:subClassOf)
    # 6. child -> parent (direct=True, from rdfs:subClassOf)
    # Indirect relationships:
    # 7. child -> grandparent (direct=False, from closure)
    ancestors = (
        db.query(models.EnvoAncestor)
        .order_by(models.EnvoAncestor.id, models.EnvoAncestor.ancestor_id)
        .all()
    )
    assert len(ancestors) == 7

    # Check specific ancestors by querying directly (more robust than index-based)
    # Check grandparent -> grandparent (self-ref)
    grandparent_self = (
        db.query(models.EnvoAncestor)
        .filter_by(id="ENVO:00000001", ancestor_id="ENVO:00000001")
        .first()
    )
    assert grandparent_self is not None
    assert grandparent_self.direct is False  # Self-refs are always direct=False

    # Check parent -> grandparent (direct)
    parent_to_grandparent = (
        db.query(models.EnvoAncestor)
        .filter_by(id="ENVO:00000428", ancestor_id="ENVO:00000001")
        .first()
    )
    assert parent_to_grandparent is not None
    assert parent_to_grandparent.direct is True

    # Check parent -> parent (self-ref)
    parent_self = (
        db.query(models.EnvoAncestor)
        .filter_by(id="ENVO:00000428", ancestor_id="ENVO:00000428")
        .first()
    )
    assert parent_self is not None
    assert parent_self.direct is False

    # Check child -> grandparent (indirect via closure)
    child_to_grandparent = (
        db.query(models.EnvoAncestor)
        .filter_by(id="ENVO:00000446", ancestor_id="ENVO:00000001")
        .first()
    )
    assert child_to_grandparent is not None
    assert child_to_grandparent.direct is False  # Key test: indirect via closure!

    # Check child -> parent (direct)
    child_to_parent = (
        db.query(models.EnvoAncestor)
        .filter_by(id="ENVO:00000446", ancestor_id="ENVO:00000428")
        .first()
    )
    assert child_to_parent is not None
    assert child_to_parent.direct is True

    # Check child -> child (self-ref)
    child_self = (
        db.query(models.EnvoAncestor)
        .filter_by(id="ENVO:00000446", ancestor_id="ENVO:00000446")
        .first()
    )
    assert child_self is not None
    assert child_self.direct is False

    # Check UBERON -> UBERON (self-ref)
    uberon_self = (
        db.query(models.EnvoAncestor)
        .filter_by(id="UBERON:0000001", ancestor_id="UBERON:0000001")
        .first()
    )
    assert uberon_self is not None
    assert uberon_self.direct is False

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
    assert child_to_grandparent.direct is False


def test_envo_load_with_biosample_fk_constraint(db: Session):
    """Test that envo.load() doesn't violate FK constraints when biosamples reference ENVO terms."""
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

    # Second load: should NOT fail due to FK constraints.
    # The upsert strategy in envo.load() should preserve the EnvoTerm rows
    envo.load(db)
    db.commit()

    # Verify ENVO terms still exist and biosample FK references are intact
    assert db.query(models.EnvoTerm).count() == 3
    db.refresh(biosample)
    assert biosample.env_broad_scale_id == "ENVO:00000001"
    assert biosample.env_broad_scale.label == "environmental system"


def test_build_envo_trees_multiple_roots(db: Session):
    """Test that build_envo_trees correctly handles multiple root nodes."""
    # Create two separate hierarchies with different roots
    # Root 1: environmental system -> biome -> terrestrial biome
    fakes.OntologyClassFactory(id="ENVO:00000001", name="environmental system", is_root=True)
    fakes.OntologyClassFactory(id="ENVO:00000428", name="biome")
    fakes.OntologyClassFactory(id="ENVO:00000446", name="terrestrial biome")

    # Root 2: material entity -> soil -> peat soil
    fakes.OntologyClassFactory(id="ENVO:00010483", name="material entity", is_root=True)
    fakes.OntologyClassFactory(id="ENVO:00001998", name="soil")
    fakes.OntologyClassFactory(id="ENVO:00005774", name="peat soil")

    # Create relationships for hierarchy 1
    fakes.OntologyRelationFactory(
        subject="ENVO:00000428", predicate="rdfs:subClassOf", object="ENVO:00000001"
    )
    fakes.OntologyRelationFactory(
        subject="ENVO:00000446", predicate="rdfs:subClassOf", object="ENVO:00000428"
    )

    # Create relationships for hierarchy 2
    fakes.OntologyRelationFactory(
        subject="ENVO:00001998", predicate="rdfs:subClassOf", object="ENVO:00010483"
    )
    fakes.OntologyRelationFactory(
        subject="ENVO:00005774", predicate="rdfs:subClassOf", object="ENVO:00001998"
    )
    db.commit()

    # Load ENVO tables
    envo.load(db)
    db.commit()

    # Create biosamples that reference terms from BOTH hierarchies
    # Set env_local_scale to None to avoid factory creating additional EnvoTerms
    envo_term_broad = db.query(models.EnvoTerm).filter_by(id="ENVO:00000446").first()
    envo_term_medium = db.query(models.EnvoTerm).filter_by(id="ENVO:00005774").first()

    fakes.BiosampleFactory(
        env_broad_scale=envo_term_broad,
        env_local_scale=None,
        env_medium=envo_term_medium,
    )
    db.commit()

    # Build the envo trees
    envo.build_envo_trees(db)

    # Verify we have multiple roots in the tree (parent_id is NULL for roots)
    root_nodes = db.query(models.EnvoTree).filter(models.EnvoTree.parent_id.is_(None)).all()
    root_ids = {node.id for node in root_nodes}

    # Both roots should be present
    assert "ENVO:00000001" in root_ids
    assert "ENVO:00010483" in root_ids

    # Verify the full tree structure was built
    all_tree_nodes = db.query(models.EnvoTree).all()
    all_ids = {node.id for node in all_tree_nodes}

    # All terms should be in the tree
    assert "ENVO:00000001" in all_ids  # root 1
    assert "ENVO:00000428" in all_ids  # biome
    assert "ENVO:00000446" in all_ids  # terrestrial biome
    assert "ENVO:00010483" in all_ids  # root 2
    assert "ENVO:00001998" in all_ids  # soil
    assert "ENVO:00005774" in all_ids  # peat soil


def test_build_envo_trees_term_with_multiple_parents(db: Session):
    """Test that a term can have multiple parents in the EnvoTree."""
    # Create a diamond hierarchy:
    #       root
    #      /    \
    #   parent1  parent2
    #      \    /
    #       child
    fakes.OntologyClassFactory(id="ENVO:ROOT", name="root", is_root=True)
    fakes.OntologyClassFactory(id="ENVO:PARENT1", name="parent1")
    fakes.OntologyClassFactory(id="ENVO:PARENT2", name="parent2")
    fakes.OntologyClassFactory(id="ENVO:CHILD", name="child")

    # Create relationships - child has TWO parents
    fakes.OntologyRelationFactory(
        subject="ENVO:PARENT1", predicate="rdfs:subClassOf", object="ENVO:ROOT"
    )
    fakes.OntologyRelationFactory(
        subject="ENVO:PARENT2", predicate="rdfs:subClassOf", object="ENVO:ROOT"
    )
    fakes.OntologyRelationFactory(
        subject="ENVO:CHILD", predicate="rdfs:subClassOf", object="ENVO:PARENT1"
    )
    fakes.OntologyRelationFactory(
        subject="ENVO:CHILD", predicate="rdfs:subClassOf", object="ENVO:PARENT2"
    )
    db.commit()

    # Load ENVO tables
    envo.load(db)
    db.commit()

    # Create a biosample referencing the child term
    # Set other env fields to None to avoid factory creating additional EnvoTerms
    envo_term_child = db.query(models.EnvoTerm).filter_by(id="ENVO:CHILD").first()
    fakes.BiosampleFactory(env_broad_scale=envo_term_child, env_local_scale=None, env_medium=None)
    db.commit()

    # Build the envo trees
    envo.build_envo_trees(db)

    # The child should appear twice in the tree - once under each parent
    child_entries = db.query(models.EnvoTree).filter_by(id="ENVO:CHILD").all()
    assert len(child_entries) == 2

    # Verify the child has both parents
    child_parent_ids = {entry.parent_id for entry in child_entries}
    assert child_parent_ids == {"ENVO:PARENT1", "ENVO:PARENT2"}

    # The root should have NULL parent_id
    root_entry = db.query(models.EnvoTree).filter_by(id="ENVO:ROOT").first()
    assert root_entry is not None
    assert root_entry.parent_id is None


def test_envo_tree_multiple_roots_structure(db: Session):
    """Test that EnvoTree correctly stores multiple root nodes from different hierarchies."""
    # Create two roots with children
    fakes.OntologyClassFactory(id="ENVO:ROOT1", name="root1", is_root=True)
    fakes.OntologyClassFactory(id="ENVO:CHILD1", name="child1")
    fakes.OntologyClassFactory(id="ENVO:ROOT2", name="root2", is_root=True)
    fakes.OntologyClassFactory(id="ENVO:CHILD2", name="child2")

    fakes.OntologyRelationFactory(
        subject="ENVO:CHILD1", predicate="rdfs:subClassOf", object="ENVO:ROOT1"
    )
    fakes.OntologyRelationFactory(
        subject="ENVO:CHILD2", predicate="rdfs:subClassOf", object="ENVO:ROOT2"
    )
    db.commit()

    envo.load(db)
    db.commit()

    # Create biosamples referencing terms from both roots
    # Set other env fields to None to avoid factory creating additional EnvoTerms
    envo_child1 = db.query(models.EnvoTerm).filter_by(id="ENVO:CHILD1").first()
    envo_child2 = db.query(models.EnvoTerm).filter_by(id="ENVO:CHILD2").first()

    fakes.BiosampleFactory(env_broad_scale=envo_child1, env_local_scale=None, env_medium=None)
    fakes.BiosampleFactory(env_broad_scale=envo_child2, env_local_scale=None, env_medium=None)
    db.commit()

    envo.build_envo_trees(db)

    # Verify the EnvoTree table has multiple roots (parent_id is NULL)
    root_entries = db.query(models.EnvoTree).filter(models.EnvoTree.parent_id.is_(None)).all()
    root_ids = {entry.id for entry in root_entries}

    # Both roots should be present
    assert "ENVO:ROOT1" in root_ids
    assert "ENVO:ROOT2" in root_ids

    # Verify each child is connected to its correct parent
    child1_entry = (
        db.query(models.EnvoTree).filter_by(id="ENVO:CHILD1", parent_id="ENVO:ROOT1").first()
    )
    assert child1_entry is not None

    child2_entry = (
        db.query(models.EnvoTree).filter_by(id="ENVO:CHILD2", parent_id="ENVO:ROOT2").first()
    )
    assert child2_entry is not None

    # Total tree entries: 2 roots + 2 children = 4
    all_entries = db.query(models.EnvoTree).all()
    assert len(all_entries) == 4
