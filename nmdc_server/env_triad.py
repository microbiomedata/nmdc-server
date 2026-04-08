"""Validation logic for the environmental triad fields (env_broad_scale, env_local_scale, env_medium).

Validates submission sample data against:
1. Curated enum permissible values from the NMDC submission schema (fast path)
2. Ontology hierarchy checks via the envo_term/envo_ancestor tables (fallback)
"""

import re
from functools import lru_cache
from importlib import resources
from typing import Any, Optional

from linkml_runtime.utils.schemaview import SchemaView
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from nmdc_server.models import (
    EnvoAncestor,
    EnvoTerm,
    OntologyClass,
)

# Return type: row_index -> {field_name -> error_string}
# Note: JSON serialization converts int keys to strings; frontend should parse accordingly
InvalidCellsByRow = dict[int, dict[str, str]]

# Regex to extract ontology ID from "label [ONTOLOGY_ID]" format
ONTOLOGY_ID_PATTERN = re.compile(r"\[([A-Za-z_]+:\d+)\]\s*$")

# Key ancestor term IDs for hierarchy checks
BIOME = "ENVO:00000428"
ENVIRONMENTAL_MATERIAL = "ENVO:00010483"
ASTRONOMICAL_BODY_PART = "ENVO:01000813"
ORGANISM_DETERMINED_ENV_SYSTEM = "ENVO:01001000"

# Environment types that have curated enum PVs in the submission schema
CONFIRMED_ENUM_PACKAGES = ["water", "soil", "sediment", "plant-associated"]

ENV_TRIAD_FIELDS = ["env_broad_scale", "env_local_scale", "env_medium"]

# Hierarchy requirements per field: (required_ancestors, disallowed_ancestors)
# required_ancestors: term must be a subclass of at least ONE of these (OR logic)
FIELD_HIERARCHY_RULES: dict[str, tuple[list[str], list[str]]] = {
    "env_broad_scale": ([BIOME, ORGANISM_DETERMINED_ENV_SYSTEM], []),
    "env_medium": ([ENVIRONMENTAL_MATERIAL], [BIOME]),
    "env_local_scale": ([ASTRONOMICAL_BODY_PART], [BIOME]),
}


def parse_ontology_id(value: str) -> Optional[str]:
    """Extract ontology ID (CURIE) from a string like 'label [ENVO:00000446]'."""
    match = ONTOLOGY_ID_PATTERN.search(value)
    if match:
        return match.group(1)
    return None


def _env_pkg_to_enum_prefix(env_pkg: str) -> str:
    """Transform env_package name to enum prefix.

    e.g. 'plant-associated' -> 'PlantAssociated'
    """
    return env_pkg.replace("-", " ").title().replace(" ", "")


@lru_cache(maxsize=1)
def _load_submission_schema_view() -> SchemaView:
    """Load and cache the NMDC submission schema as a SchemaView."""
    submission_schema_files = resources.files("nmdc_submission_schema")
    schema_path = submission_schema_files / "schema/nmdc_submission_schema.yaml"
    return SchemaView(str(schema_path))


@lru_cache(maxsize=1)
def fetch_submission_schema_enums() -> dict[str, frozenset[str]]:
    """Load env-related enum PVs from the NMDC submission schema.

    Returns a dict mapping enum name -> frozenset of permissible value strings.
    Results are cached; call fetch_submission_schema_enums.cache_clear() to invalidate.
    """
    sv = _load_submission_schema_view()
    enum_view = sv.all_enums()

    return {
        enum_name: frozenset(enum_data["permissible_values"].keys())
        for enum_name, enum_data in enum_view.items()
        if ("EnvPackage" in enum_name)
        or ("EnvMedium" in enum_name)
        or ("EnvBroadScale" in enum_name)
        or ("EnvLocalScale" in enum_name)
    }


@lru_cache(maxsize=1)
def _fetch_schema_field_patterns() -> dict[str, dict[str, re.Pattern]]:
    """Load per-interface regex patterns for env triad fields from the submission schema.

    Parses slot_usage from each *Interface class to extract field-level regex patterns.
    Returns a dict mapping interface_class_name -> field_name -> compiled regex pattern.
    """
    sv = _load_submission_schema_view()

    result: dict[str, dict[str, re.Pattern]] = {}
    for class_name, class_def in sv.all_classes().items():
        if not class_name.endswith("Interface"):
            continue
        slot_usage = class_def.slot_usage or {}
        field_patterns: dict[str, re.Pattern] = {}
        for field_name in ENV_TRIAD_FIELDS:
            if field_name in slot_usage:
                pattern_str = slot_usage[field_name].pattern
                if pattern_str:
                    field_patterns[field_name] = re.compile(pattern_str)
        if field_patterns:
            result[class_name] = field_patterns

    return result


def _template_type_to_interface_name(template_type: str) -> str:
    """Convert template_type to schema interface class name.

    e.g. 'plant_associated_data' -> 'PlantAssociatedInterface'
    """
    base = template_type.removesuffix("_data")
    camel = base.replace("_", " ").title().replace(" ", "")
    return f"{camel}Interface"


def _matches_schema_field_pattern(value: str, field_name: str, template_type: str) -> bool:
    """Check if value matches the schema regex pattern for this template+field.

    Used as a last-resort fallback to allow non-ENVO terms that match the schema's
    expected format (e.g. PO terms for plant-associated, UBERON for host-associated).
    """
    interface_name = _template_type_to_interface_name(template_type)
    patterns = _fetch_schema_field_patterns()
    interface_patterns = patterns.get(interface_name, {})
    pattern = interface_patterns.get(field_name)
    if pattern is None:
        return False
    return bool(pattern.match(value))


def _check_enum_membership(
    value: str, field_name: str, env_pkg: str, schema_enums: dict[str, frozenset[str]]
) -> bool:
    """Check if value is in the curated enum PV list for this environment type + field.

    Returns True if the value is found in the appropriate enum (term is pre-vetted).
    Returns False if no matching enum exists or the value is not in it.
    """
    if env_pkg not in CONFIRMED_ENUM_PACKAGES:
        return False

    prefix = _env_pkg_to_enum_prefix(env_pkg)

    field_to_enum_prefix = {
        "env_broad_scale": "EnvBroadScale",
        "env_local_scale": "EnvLocalScale",
        "env_medium": "EnvMedium",
    }
    enum_prefix = field_to_enum_prefix.get(field_name)
    if not enum_prefix:
        return False

    enum_name = f"{enum_prefix}{prefix}Enum"
    pvs: frozenset[str] = schema_enums.get(enum_name, frozenset())
    return value in pvs


class _PrefetchedTermData(BaseModel):
    """Batch-fetched term data for efficient validation.

    Three lookup dicts keyed by ontology ID (e.g. "ENVO:00000428"):
      exists    -> bool   (is the term in the DB?)
      obsolete  -> bool   (is the term obsolete?)
      ancestors -> set    (ancestor term IDs for hierarchy checks)

    Populated once by _prefetch_term_data(), then read by _validate_field().
    """

    model_config = {"arbitrary_types_allowed": True}

    # term_id -> True if term exists
    exists: dict[str, bool] = Field(default_factory=dict)
    # term_id -> True if term is obsolete
    obsolete: dict[str, bool] = Field(default_factory=dict)
    # term_id -> set of ancestor_ids
    ancestors: dict[str, set[str]] = Field(default_factory=dict)


def _prefetch_term_data(db: Session, ontology_ids: set[str]) -> _PrefetchedTermData:
    """Batch-fetch term existence, obsolete status, and ancestors for a set of ontology IDs."""
    result = _PrefetchedTermData()
    if not ontology_ids:
        return result

    # Query 1: Check envo_term for existence and obsolete status
    envo_terms = db.query(EnvoTerm.id, EnvoTerm.data).filter(EnvoTerm.id.in_(ontology_ids)).all()
    found_ids = set()
    for term_id, data in envo_terms:
        found_ids.add(term_id)
        result.exists[term_id] = True
        result.obsolete[term_id] = bool(data.get("is_obsolete", False)) if data else False

    # For IDs not found in envo_term, check ontology_class (covers PO, UBERON, etc.)
    missing_ids = ontology_ids - found_ids
    if missing_ids:
        oc_terms = (
            db.query(OntologyClass.id, OntologyClass.is_obsolete)
            .filter(OntologyClass.id.in_(missing_ids))
            .all()
        )
        for term_id, is_obsolete in oc_terms:
            found_ids.add(term_id)
            result.exists[term_id] = True
            result.obsolete[term_id] = bool(is_obsolete)

    # Mark truly missing IDs
    for term_id in ontology_ids - found_ids:
        result.exists[term_id] = False

    # Query 2: Get all ancestor relationships for found terms
    if found_ids:
        ancestor_rows = (
            db.query(EnvoAncestor.id, EnvoAncestor.ancestor_id)
            .filter(EnvoAncestor.id.in_(found_ids))
            .all()
        )
        for term_id, ancestor_id in ancestor_rows:
            if term_id not in result.ancestors:
                result.ancestors[term_id] = set()
            result.ancestors[term_id].add(ancestor_id)

    return result


def _validate_field(
    field_name: str,
    value: Optional[Any],
    template_type: str,
    env_pkg: str,
    schema_enums: dict[str, frozenset[str]],
    prefetched: _PrefetchedTermData,
) -> Optional[str]:
    """Validate a single env triad field value.

    Returns an error string if invalid, or None if valid.
    """
    # Skip validation for empty values (required check handled by harmonizer)
    if value is None:
        return None
    str_value = str(value).strip()
    if not str_value:
        return None

    # Clean the value (strip leading underscores and whitespace, matching mixs_report pattern)
    cleaned = str_value.lstrip("_")

    # Step 1: Enum PV check (fast path)
    if _check_enum_membership(cleaned, field_name, env_pkg, schema_enums):
        return None

    # Step 2: Ontology fallback checks
    ontology_id = parse_ontology_id(cleaned)
    if ontology_id is None:
        return (
            f"Could not parse ontology ID from '{cleaned}'. "
            "Expected format: 'label [ONTOLOGY_PREFIX:ID]'"
        )

    # Check term exists
    if not prefetched.exists.get(ontology_id, False):
        return f"Term '{ontology_id}' not found in ontology database"

    errors: list[str] = []

    # Check not obsolete
    if prefetched.obsolete.get(ontology_id, False):
        errors.append(f"Term '{ontology_id}' is obsolete")

    # Hierarchy checks
    term_ancestors = prefetched.ancestors.get(ontology_id, set())
    required_ancestors, disallowed_ancestors = FIELD_HIERARCHY_RULES.get(
        field_name, ([], [])
    )

    if required_ancestors:
        if not any(ancestor in term_ancestors for ancestor in required_ancestors):
            # Hierarchy check failed. For non-ENVO terms, fall back to the schema's
            # regex pattern for this template+field as a last resort. This allows
            # ontologies like PO (plant-associated) or UBERON (host-associated)
            # when the schema explicitly permits them.
            prefix = ontology_id.split(":")[0] if ":" in ontology_id else ""
            if prefix == "ENVO" or not _matches_schema_field_pattern(
                cleaned, field_name, template_type
            ):
                ancestor_labels = {
                    BIOME: "biome (ENVO:00000428)",
                    ENVIRONMENTAL_MATERIAL: "environmental material (ENVO:00010483)",
                    ASTRONOMICAL_BODY_PART: "astronomical body part (ENVO:01000813)",
                    ORGANISM_DETERMINED_ENV_SYSTEM: (
                        "environmental system determined by an organism (ENVO:01001000)"
                    ),
                }
                labels = [
                    ancestor_labels.get(a, a) for a in required_ancestors
                ]
                label = " or ".join(labels)
                errors.append(f"Term '{ontology_id}' is not a subclass of {label}")

    for disallowed in disallowed_ancestors:
        if disallowed in term_ancestors and ontology_id != disallowed:
            disallowed_labels = {
                BIOME: "biome (ENVO:00000428)",
            }
            label = disallowed_labels.get(disallowed, disallowed)
            errors.append(f"Term '{ontology_id}' should not be a subclass of {label}")

    return "; ".join(errors) if errors else None


def _validate_sample_triad(
    sample: dict[str, Any],
    template_type: str,
    env_pkg: str,
    schema_enums: dict[str, frozenset[str]],
    prefetched: _PrefetchedTermData,
) -> dict[str, str]:
    """Validate all three env triad fields for a single sample.

    Returns a dict of field_name -> error_string for fields with errors.
    Empty dict means all fields are valid.
    """
    field_errors: dict[str, str] = {}

    for field_name in ENV_TRIAD_FIELDS:
        value = sample.get(field_name)
        error = _validate_field(field_name, value, template_type, env_pkg, schema_enums, prefetched)
        if error:
            field_errors[field_name] = error

    # Cross-field check: no duplicate ontology IDs across the three triad slots
    seen_ids: dict[str, str] = {}
    for field_name in ENV_TRIAD_FIELDS:
        value = sample.get(field_name)
        if value:
            ontology_id = parse_ontology_id(str(value).strip().lstrip("_"))
            if ontology_id:
                if ontology_id in seen_ids:
                    cross_error = (
                        f"Ontology term '{ontology_id}' is used in both "
                        f"{seen_ids[ontology_id]} and {field_name}"
                    )
                    existing = field_errors.get(field_name, "")
                    field_errors[field_name] = (
                        f"{existing}; {cross_error}" if existing else cross_error
                    )
                else:
                    seen_ids[ontology_id] = field_name

    return field_errors


def _collect_ids_from_samples(
    samples: list[dict[str, Any]], schema_enums: dict[str, frozenset[str]], env_pkg: str
) -> set[str]:
    """Collect ontology IDs that need DB lookup from a flat list of samples."""
    ids_needing_lookup: set[str] = set()
    for sample in samples:
        for field_name in ENV_TRIAD_FIELDS:
            value = sample.get(field_name)
            if not value or not str(value).strip():
                continue
            cleaned = str(value).strip().lstrip("_")
            if _check_enum_membership(cleaned, field_name, env_pkg, schema_enums):
                continue
            ontology_id = parse_ontology_id(cleaned)
            if ontology_id:
                ids_needing_lookup.add(ontology_id)
    return ids_needing_lookup


def validate_sample_data_triad(
    db: Session,
    samples: list[dict[str, Any]],
    env_package: str,
    template_type: str,
) -> InvalidCellsByRow:
    """Validate env triad fields for a list of samples.

    Returns a dict of row_index -> {field_name -> error_string}.
    Empty dict means all fields are valid.
    """
    if not samples:
        return {}

    schema_enums = fetch_submission_schema_enums()

    # First pass: collect IDs needing DB lookup, then batch prefetch
    ids_needing_lookup = _collect_ids_from_samples(samples, schema_enums, env_package)
    prefetched = _prefetch_term_data(db, ids_needing_lookup)

    # Second pass: validate each sample
    result: InvalidCellsByRow = {}

    for i, sample in enumerate(samples):
        field_errors = _validate_sample_triad(
            sample, template_type, env_package, schema_enums, prefetched
        )
        if field_errors:
            result[i] = field_errors

    return result
