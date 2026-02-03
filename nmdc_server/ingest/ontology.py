"""ETL script to load generic ontology data from MongoDB to PostgreSQL."""

import logging
from typing import Dict, List, Set

from pymongo.cursor import Cursor
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from nmdc_server.ingest.common import extract_extras
from nmdc_server.models import OntologyClass, OntologyRelation
from nmdc_server.schemas import OntologyClassCreate

logger = logging.getLogger(__name__)


class OntologyClassLoader(OntologyClassCreate):
    """Pydantic model for validating and transforming OntologyClass documents from MongoDB."""

    @property
    def ontology_prefix(self) -> str:
        """Extract the ontology prefix from the ID (e.g., 'ENVO' from 'ENVO:00000001')."""
        return self.id.split(":")[0] if ":" in self.id else ""

    @classmethod
    def from_mongo(cls, doc: Dict) -> "OntologyClassLoader":
        """Create an OntologyClassLoader from a MongoDB document.

        Handles the transformation from MongoDB's schema to our PostgreSQL schema.
        """
        # Remove relations field if present (not stored in OntologyClass table)
        doc.pop("relations", None)

        # Transform the document
        transformed = {
            "id": doc.get("id"),
            "type": doc.get("type", "nmdc:OntologyClass"),
            "name": doc.get("name", ""),
            "definition": doc.get("definition"),  # Preserve NULL semantics
            "alternative_names": doc.get("alternative_names", []),
            "is_root": doc.get("is_root", False),
            "is_obsolete": doc.get("is_obsolete", False),
        }

        # Extract any extra fields into annotations
        transformed = extract_extras(cls, transformed, exclude={"relations"})  # type: ignore[arg-type]

        return cls(**transformed)


def load_ontology_classes(db: Session, cursor: Cursor) -> Dict[str, Set[str]]:
    """Load ontology classes from MongoDB cursor into PostgreSQL.

    Returns:
        Dict mapping ontology prefixes to sets of loaded class IDs
    """
    logger.info("Loading ontology classes...")

    loaded_classes: Dict[str, Set[str]] = {}
    batch = []
    batch_size = 1000
    total_count = 0

    for doc in cursor:
        try:
            # Transform the document
            ontology_class = OntologyClassLoader.from_mongo(doc)

            # Track loaded classes by prefix
            prefix = ontology_class.ontology_prefix
            if prefix not in loaded_classes:
                loaded_classes[prefix] = set()
            loaded_classes[prefix].add(ontology_class.id)

            batch.append(ontology_class.model_dump())

            # Bulk insert when batch is full
            if len(batch) >= batch_size:
                _bulk_upsert_classes(db, batch)
                total_count += len(batch)
                logger.info(f"Loaded {total_count} ontology classes...")
                batch = []

        except Exception as e:
            logger.error(f"Error loading ontology class {doc.get('id', 'unknown')}: {e}")
            continue

    # Insert remaining batch
    if batch:
        _bulk_upsert_classes(db, batch)
        total_count += len(batch)

    logger.info(f"Finished loading {total_count} ontology classes")

    # Log summary by ontology
    for prefix, ids in loaded_classes.items():
        logger.info(f"  {prefix}: {len(ids)} classes")

    return loaded_classes


def _bulk_upsert_classes(db: Session, classes: List[Dict]) -> None:
    """Bulk upsert ontology classes using PostgreSQL's ON CONFLICT.

    Note: This function does not commit. The caller is responsible for
    committing the transaction to ensure atomicity across all batches.
    """
    if not classes:
        return

    stmt = insert(OntologyClass).values(classes)
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={
            "name": stmt.excluded.name,
            "definition": stmt.excluded.definition,
            "alternative_names": stmt.excluded.alternative_names,
            "is_root": stmt.excluded.is_root,
            "is_obsolete": stmt.excluded.is_obsolete,
            "annotations": stmt.excluded.annotations,
        },
    )
    db.execute(stmt)


def load_ontology_relations(
    db: Session, cursor: Cursor, loaded_classes: Dict[str, Set[str]]
) -> None:
    """Load ontology relations from MongoDB cursor into PostgreSQL.

    Args:
        db: SQLAlchemy session
        cursor: MongoDB cursor for ontology_relation_set
        loaded_classes: Dict mapping prefixes to loaded class IDs
    """
    logger.info("Loading ontology relations...")

    batch = []
    batch_size = 5000
    total_count = 0
    skipped_count = 0

    # Flatten loaded classes for easier lookup
    all_loaded_ids = set()
    for ids in loaded_classes.values():
        all_loaded_ids.update(ids)

    for doc in cursor:
        try:
            subject = doc.get("subject")
            predicate = doc.get("predicate")
            obj = doc.get("object")

            # Skip if required fields are missing
            if not all([subject, predicate, obj]):
                skipped_count += 1
                continue

            # Only include relations where both subject and object exist in our loaded classes
            # (FK constraints require both to be valid references)
            if subject not in all_loaded_ids or obj not in all_loaded_ids:
                skipped_count += 1
                continue

            relation = {
                "subject": subject,
                "predicate": predicate,
                "object": obj,
                "type": doc.get("type", "nmdc:OntologyRelation"),
            }

            batch.append(relation)

            # Bulk insert when batch is full
            if len(batch) >= batch_size:
                _bulk_insert_relations(db, batch)
                total_count += len(batch)
                logger.info(f"Loaded {total_count} ontology relations...")
                batch = []

        except Exception as e:
            logger.error(f"Error loading ontology relation: {e}")
            skipped_count += 1
            continue

    # Insert remaining batch
    if batch:
        _bulk_insert_relations(db, batch)
        total_count += len(batch)

    logger.info(f"Finished loading {total_count} ontology relations (skipped {skipped_count})")


def _bulk_insert_relations(db: Session, relations: List[Dict]) -> None:
    """Bulk insert ontology relations, ignoring conflicts.

    Note: This function does not commit. The caller is responsible for
    committing the transaction to ensure atomicity across all batches.
    """
    if not relations:
        return

    stmt = insert(OntologyRelation).values(relations)
    # Use on_conflict_do_nothing since we have a unique constraint on (subject, predicate, object)
    stmt = stmt.on_conflict_do_nothing(index_elements=["subject", "predicate", "object"])
    db.execute(stmt)


def load(db: Session, class_cursor: Cursor, relation_cursor: Cursor):
    """Main entry point for loading ontology data.

    Args:
        db: SQLAlchemy session
        class_cursor: MongoDB cursor for ontology_class_set
        relation_cursor: MongoDB cursor for ontology_relation_set
    """
    # Load ontology classes
    loaded_classes = load_ontology_classes(db, class_cursor)

    # Load ontology relations
    load_ontology_relations(db, relation_cursor, loaded_classes)
