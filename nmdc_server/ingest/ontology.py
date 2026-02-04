"""ETL script to load generic ontology data from MongoDB to PostgreSQL."""

from typing import Dict, List, Set

from pydantic import model_validator
from pymongo.cursor import Cursor
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from nmdc_server.ingest.common import ETLReport, extract_extras
from nmdc_server.ingest.errors import errors
from nmdc_server.logger import get_logger
from nmdc_server.models import OntologyClass, OntologyRelation
from nmdc_server.schemas import OntologyClassCreate

logger = get_logger(__name__)


class OntologyClassLoader(OntologyClassCreate):
    @classmethod
    @model_validator(mode="before")
    def extract_extras(cls, values):
        # Remove relations field if present (not stored in OntologyClass table)
        values.pop("relations", None)
        return extract_extras(cls, values, exclude={"relations"})  # type: ignore

    @property
    def ontology_prefix(self) -> str:
        return self.id.split(":")[0] if ":" in self.id else ""


def load_ontology_classes(db: Session, cursor: Cursor, report: ETLReport) -> Dict[str, Set[str]]:
    logger.info("Loading ontology classes...")

    loaded_classes: Dict[str, Set[str]] = {}
    batch = []
    batch_size = 1000

    for doc in cursor:
        report.num_extracted += 1
        try:
            ontology_class = OntologyClassLoader(**doc)

            # Track loaded classes by prefix
            prefix = ontology_class.ontology_prefix
            if prefix not in loaded_classes:
                loaded_classes[prefix] = set()
            loaded_classes[prefix].add(ontology_class.id)

            batch.append(ontology_class.model_dump())

            # Bulk insert when batch is full
            if len(batch) >= batch_size:
                _bulk_upsert_classes(db, batch)
                report.num_loaded += len(batch)
                logger.info(f"Loaded {report.num_loaded} ontology classes...")
                batch = []

        except Exception as e:
            logger.error(f"Error loading ontology class {doc.get('id', 'unknown')}: {e}")
            errors["ontology_class"].add(doc.get("id", "unknown"))
            continue

    # Insert remaining batch
    if batch:
        _bulk_upsert_classes(db, batch)
        report.num_loaded += len(batch)

    logger.info(f"Finished loading {report.num_loaded} ontology classes")

    # Log summary by ontology
    for prefix, ids in loaded_classes.items():
        logger.info(f"  {prefix}: {len(ids)} classes")

    return loaded_classes


def _bulk_upsert_classes(db: Session, classes: List[Dict]) -> None:
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
) -> int:
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
            errors["ontology_relation"].add(f"{doc.get('subject')}->{doc.get('object')}")
            skipped_count += 1
            continue

    # Insert remaining batch
    if batch:
        _bulk_insert_relations(db, batch)
        total_count += len(batch)

    logger.info(f"Finished loading {total_count} ontology relations (skipped {skipped_count})")
    return total_count


def _bulk_insert_relations(db: Session, relations: List[Dict]) -> None:
    if not relations:
        return

    stmt = insert(OntologyRelation).values(relations)
    # Use on_conflict_do_nothing since we have a unique constraint on (subject, predicate, object)
    stmt = stmt.on_conflict_do_nothing(index_elements=["subject", "predicate", "object"])
    db.execute(stmt)


def load(db: Session, class_cursor: Cursor, relation_cursor: Cursor) -> ETLReport:
    report = ETLReport(plural_subject="OntologyClasses")

    # Truncate ontology tables before reload to avoid:
    # 1. Burning sequence values with ON CONFLICT DO NOTHING
    # 2. Accumulating stale data from removed ontology entries
    # Note: Must truncate relations first due to FK constraints
    logger.info("Truncating ontology tables for fresh reload...")
    db.execute(text("TRUNCATE TABLE ontology_relation RESTART IDENTITY"))
    db.execute(text("TRUNCATE TABLE ontology_class CASCADE"))

    # Load ontology classes
    loaded_classes = load_ontology_classes(db, class_cursor, report)

    # Load ontology relations
    load_ontology_relations(db, relation_cursor, loaded_classes)

    return report
