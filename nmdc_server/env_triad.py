"""Validation logic for the environmental triad fields (env_broad_scale, env_local_scale, env_medium).

Validates submission sample data against:
1. Curated enum permissible values from the NMDC submission schema (fast path)
2. Ontology hierarchy checks via the envo_term/envo_ancestor tables (fallback)
"""

import re
from functools import cache
from importlib import resources
from typing import Any, Optional

from linkml_runtime.utils.schemaview import SchemaView
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from nmdc_server.models import (
    ENVIRONMENTAL_DATA_SLOTS,
    EnvoAncestor,
    EnvoTerm,
    OntologyClass,
)

# Return type: template_name -> {row_index -> {field_name -> error_string}}
InvalidCellsByTemplate = dict[str, dict[int, dict[str, str]]]

# Regex to extract ontology ID from "label [ONTOLOGY_ID]" format
ONTOLOGY_ID_PATTERN = re.compile(r"\[([A-Za-z_]+:\d+)\]\s*$")

# Key ancestor term IDs for hierarchy checks
BIOME = "ENVO:00000428"
ENVIRONMENTAL_MATERIAL = "ENVO:00010483"
ASTRONOMICAL_BODY_PART = "ENVO:01000813"

# Environment types that have curated enum PVs in the submission schema
CONFIRMED_ENUM_PACKAGES = ["water", "soil", "sediment", "plant-associated"]

# Non-ENVO prefixes allowed for env_local_scale per template type
LOCAL_SCALE_EXTRA_PREFIXES: dict[str, list[str]] = {
    "plant_associated_data": ["PO"],
    "host_associated_data": ["UBERON"],
}

ENV_TRIAD_FIELDS = ["env_broad_scale", "env_local_scale", "env_medium"]

# Hierarchy requirements per field: (required_ancestor, disallowed_ancestors)
FIELD_HIERARCHY_RULES: dict[str, tuple[str, list[str]]] = {
    "env_broad_scale": (BIOME, []),
    "env_medium": (ENVIRONMENTAL_MATERIAL, [BIOME]),
    "env_local_scale": (ASTRONOMICAL_BODY_PART, [BIOME]),
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


@cache
def fetch_submission_schema_enums() -> dict[str, frozenset[str]]:
    """Load env-related enum PVs from the NMDC submission schema.

    Returns a dict mapping enum name -> frozenset of permissible value strings.
    Results are cached for the lifetime of the process.
    """
    submission_schema_files = resources.files("nmdc_submission_schema")
    schema_path = submission_schema_files / "schema/nmdc_submission_schema.yaml"
    sv = SchemaView(str(schema_path))
    enum_view = sv.all_enums()

    return {
        enum_name: frozenset(enum_data["permissible_values"].keys())
        for enum_name, enum_data in enum_view.items()
        if ("EnvPackage" in enum_name)
        or ("EnvMedium" in enum_name)
        or ("EnvBroadScale" in enum_name)
        or ("EnvLocalScale" in enum_name)
    }


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
    pvs = schema_enums.get(enum_name, frozenset())
    return value in pvs


class _PrefetchedTermData(BaseModel):
    """Batch-fetched term data for efficient validation."""

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
    value: Optional[str],
    template_type: str,
    env_pkg: str,
    schema_enums: dict[str, frozenset[str]],
    prefetched: _PrefetchedTermData,
) -> Optional[str]:
    """Validate a single env triad field value.

    Returns an error/warning string if invalid, or None if valid.
    """
    # Step 0: Required check
    if not value or not value.strip():
        return f"{field_name} is required"

    # Clean the value (strip leading underscores and whitespace, matching mixs_report pattern)
    cleaned = value.strip().lstrip("_")

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
    required_ancestor, disallowed_ancestors = FIELD_HIERARCHY_RULES.get(field_name, (None, []))

    if required_ancestor:
        # For env_local_scale, allow non-ENVO terms from permitted ontologies
        prefix = ontology_id.split(":")[0] if ":" in ontology_id else ""
        allowed_prefixes = LOCAL_SCALE_EXTRA_PREFIXES.get(template_type, [])

        if field_name == "env_local_scale" and prefix in allowed_prefixes:
            # Non-ENVO term from an allowed ontology — skip hierarchy check
            pass
        elif required_ancestor not in term_ancestors:
            ancestor_labels = {
                BIOME: "biome (ENVO:00000428)",
                ENVIRONMENTAL_MATERIAL: "environmental material (ENVO:00010483)",
                ASTRONOMICAL_BODY_PART: "astronomical body part (ENVO:01000813)",
            }
            label = ancestor_labels.get(required_ancestor, required_ancestor)
            errors.append(f"Term '{ontology_id}' is not a subclass of {label}")

    for disallowed in disallowed_ancestors:
        if disallowed in term_ancestors and ontology_id != disallowed:
            disallowed_labels = {
                BIOME: "biome (ENVO:00000428)",
            }
            label = disallowed_labels.get(disallowed, disallowed)
            errors.append(f"Term '{ontology_id}' should not be a subclass of {label}")

    # If the term passed ontology checks but wasn't in the enum, add a warning
    if not errors and env_pkg in CONFIRMED_ENUM_PACKAGES:
        errors.append(
            f"Term '{ontology_id}' is not in the curated permissible values "
            f"for {env_pkg} {field_name}"
        )

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


def _collect_ids_needing_lookup(sample_data: dict, schema_enums: dict, env_pkg: str) -> set[str]:
    """First pass: collect ontology IDs that need DB lookup (didn't pass enum check)."""
    ids_needing_lookup: set[str] = set()
    for template_type in sample_data:
        if template_type not in ENVIRONMENTAL_DATA_SLOTS:
            continue
        samples = sample_data[template_type] or []
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


def validate_submission_triad(db: Session, submission: Any) -> InvalidCellsByTemplate:
    """Validate all env triad fields across all samples in a submission.

    Returns a dict of template_name -> {row_index -> {field_name -> error_string}}.
    Empty dict means all fields are valid.
    """
    metadata = submission.metadata_submission or {}
    sample_data = metadata.get("sampleData", {})
    env_pkg = metadata.get("packageName", "")

    # If packageName is a list, take the first element
    if isinstance(env_pkg, list):
        env_pkg = env_pkg[0] if env_pkg else ""

    # Load schema enums once
    schema_enums = fetch_submission_schema_enums()

    # First pass: collect IDs needing DB lookup, then batch prefetch
    ids_needing_lookup = _collect_ids_needing_lookup(sample_data, schema_enums, env_pkg)
    prefetched = _prefetch_term_data(db, ids_needing_lookup)

    # Second pass: validate each sample
    result: InvalidCellsByTemplate = {}

    for template_type in sample_data:
        if template_type not in ENVIRONMENTAL_DATA_SLOTS:
            continue
        samples = sample_data[template_type] or []
        for i, sample in enumerate(samples):
            field_errors = _validate_sample_triad(
                sample, template_type, env_pkg, schema_enums, prefetched
            )
            if field_errors:
                if template_type not in result:
                    result[template_type] = {}
                result[template_type][i] = field_errors

    return result
