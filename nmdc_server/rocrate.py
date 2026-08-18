from datetime import datetime
from pathlib import PurePosixPath
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from nmdc_server import models
from nmdc_server.utils import safe_name

IDENTIFIER_PREFIX_URL = "https://bioregistry.io"


def get_rocrate_base_bulk_download():
    """
    Base RO-Crate structure with placeholders for dynamic content.
    This gets included in bulk downloads as ro-crate-metadata.json.
    See https://www.researchobject.org/ro-crate/specification/1.2/introduction.html
    """
    return {
        "@context": [
            "https://w3id.org/ro/crate/1.2/context",
            {"nmdc": "https://w3id.org/nmdc/"},
        ],
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "conformsTo": {"@id": "https://w3id.org/ro/crate/1.2"},
                "about": {"@id": "./"},
            },
            {
                "@id": "./",
                "@type": "Dataset",
                "name": "NMDC Data Portal Bulk Download",
                "description": "autogenerate-me",
                "datePublished": "autogenerate-me",
                "license": "https://creativecommons.org/licenses/by/4.0/",
                "additionalProperty": [
                    {
                        "@type": "PropertyValue",
                        "name": "query_conditions",
                        "value": ["autogenerate-me"],
                    },
                    {
                        "@type": "PropertyValue",
                        "name": "selected_file_types",
                        "value": ["autogenerate-me"],
                    },
                ],
                "hasPart": [
                    {"@id": "README.md"},
                    {"@id": "metadata/"},
                    {"@id": "metadata/data_objects.json"},
                    {"@id": "data/"},
                ],
            },
            {
                "@id": "README.md",
                "@type": "File",
                "description": "Human-readable summary of how to navigate this bulk download.",
            },
            {
                "@id": "metadata/",
                "@type": "Dataset",
                "name": "Metadata Directory",
                "description": "Metadata files that associate the data files in this bulk download with other NMDC research entities.",
                "hasPart": [{"@id": "metadata/data_objects.json"}],
            },
            {
                "@id": "metadata/data_objects.json",
                "@type": "File",
                "name": "Data Object Metadata",
                "description": "A JSON array containing metadata, archive paths, and related Biosample IDs for the DataObjects included in this download.",
            },
            {
                "@id": "data/",
                "@type": "Dataset",
                "name": "Data Directory",
                "description": "autogenerate-me",
            },
        ],
    }


def get_root_data_entity(rocrate_dict):
    """Helper function to extract the root data entity from the RO-Crate dictionary."""
    return next((item for item in rocrate_dict["@graph"] if item["@id"] == "./"), None)


def _get_related_documents(
    db: Session, ids: list[str]
) -> dict[str, models.BiosampleRelatedDocument]:
    rows = db.execute(
        select(models.BiosampleRelatedDocument).where(models.BiosampleRelatedDocument.id.in_(ids))
    ).scalars()
    return {row.id: row for row in rows}


def _references(ids):
    return [{"@id": id_} for id_ in sorted(dict.fromkeys(ids))]


def _overlap(left: list[str], right: list[str]) -> bool:
    """Return whether two ID lists contain at least one ID in common."""
    return any(id_ in right for id_ in left)


def _document(row: models.BiosampleRelatedDocument) -> dict[str, Any]:
    return cast(dict[str, Any], row.document)


def _add_archive_entities(
    graph: list[dict[str, Any]],
    data_directory_entity: dict[str, Any],
    bulk_download: models.BulkDownload,
    precise_entity_ids: list[str],
) -> None:
    """
    Describe the physical data hierarchy and connect it to NMDC entities.
    This currently only describes the structure down to the WorkflowExecution directory level.
    We do this to minimize the RO-Crate size and because DataObject metadata is included in `metadata/data_objects.json`.
    """
    id_by_archive_name = {safe_name(id_): id_ for id_ in precise_entity_ids}
    directories: dict[str, dict[str, Any]] = {}

    for download_file in bulk_download.files:
        path = PurePosixPath(download_file.path)
        if len(path.parts) != 4 or path.parts[0] != "data":
            continue

        _, data_generation_name, workflow_execution_name, _ = path.parts
        data_generation_dir_id = f"data/{data_generation_name}/"
        workflow_execution_dir_id = f"{data_generation_dir_id}{workflow_execution_name}/"

        data_generation_dir_node = directories.setdefault(
            data_generation_dir_id,
            {"@id": data_generation_dir_id, "@type": "Dataset", "hasPart": []},
        )
        workflow_execution_dir_node = directories.setdefault(
            workflow_execution_dir_id,
            {"@id": workflow_execution_dir_id, "@type": "Dataset", "hasPart": []},
        )

        precise_data_generation_id = id_by_archive_name.get(data_generation_name)
        if precise_data_generation_id is not None:
            data_generation_dir_node["about"] = {"@id": precise_data_generation_id}
        precise_workflow_execution_id = id_by_archive_name.get(workflow_execution_name)
        if precise_workflow_execution_id is not None:
            workflow_execution_dir_node["about"] = {"@id": precise_workflow_execution_id}

        data_generation_dir_reference = {"@id": data_generation_dir_id}
        if data_generation_dir_reference not in data_directory_entity.setdefault("hasPart", []):
            data_directory_entity["hasPart"].append(data_generation_dir_reference)
        workflow_execution_dir_reference = {"@id": workflow_execution_dir_id}
        if workflow_execution_dir_reference not in data_generation_dir_node["hasPart"]:
            data_generation_dir_node["hasPart"].append(workflow_execution_dir_reference)

    for entity in directories.values():
        if entity["hasPart"]:
            entity["hasPart"].sort(key=lambda reference: reference["@id"])
        else:
            del entity["hasPart"]
    data_directory_entity.setdefault("hasPart", []).sort(key=lambda reference: reference["@id"])
    graph.extend(directories[id_] for id_ in sorted(directories))


def _get_data_generation_and_workflow_executions(
    db: Session, output_ids: list[str]
) -> dict[str, models.BiosampleRelatedDocument]:
    rows = db.execute(
        select(models.BiosampleRelatedDocument)
        .where(
            models.BiosampleRelatedDocument.high_level_type.in_(
                ["nmdc:DataGeneration", "nmdc:WorkflowExecution"]
            )
        )
        .where(
            models.BiosampleRelatedDocument.document["has_output"].op("?|")(
                postgresql.array(output_ids)  # type: ignore[call-overload]
            )
        )
    ).scalars()
    return {row.id: row for row in rows}


def generate_rocrate_for_bulk_download(  # noqa: C901
    db: Session, bulk_download: models.BulkDownload, data_object_ids: list[str]
):
    """Generates an RO-Crate metadata object for a given bulk download record."""
    rocrate_dict = get_rocrate_base_bulk_download()
    root_data_entity = get_root_data_entity(rocrate_dict)
    if not root_data_entity:
        raise ValueError("RO-Crate structure is missing the root data entity with @id './'")
    root_data_entity["datePublished"] = bulk_download.created.isoformat()
    root_data_entity["description"] = (
        f"Bulk download of data files from the NMDC Data Portal, generated on {datetime.now().strftime("%Y-%m-%d")} at {datetime.now().strftime("%H:%M")}. The files included in the data directory are determined by the `query_conditions` and `selected_file_types` specified for this bulk download."
    )
    query_conditions_property = next(
        (
            prop
            for prop in root_data_entity["additionalProperty"]
            if prop["name"] == "query_conditions"
        ),
        None,
    )
    if not query_conditions_property:
        raise ValueError("RO-Crate structure is missing the 'query_conditions' additional property")
    query_conditions_property["value"] = bulk_download.conditions
    selected_file_types_property = next(
        (
            prop
            for prop in root_data_entity["additionalProperty"]
            if prop["name"] == "selected_file_types"
        ),
        None,
    )
    if not selected_file_types_property:
        raise ValueError(
            "RO-Crate structure is missing the 'selected_file_types' additional property"
        )
    selected_file_types_property["value"] = bulk_download.filter
    data_directory_entity = next(
        (item for item in rocrate_dict["@graph"] if item["@id"] == "data/"), None
    )
    if not data_directory_entity:
        raise ValueError("RO-Crate structure is missing the data directory entity with @id 'data/'")
    data_directory_entity["description"] = (
        f"Directory containing the {len(data_object_ids)} data files for this bulk download. "
        "Files are organized by DataGeneration and WorkflowExecution."
    )

    data_object_rows = _get_related_documents(db, list(dict.fromkeys(data_object_ids)))
    dg_and_wfe_rows: dict[str, models.BiosampleRelatedDocument] = {}
    pending_output_ids = list(dict.fromkeys(data_object_ids))
    visited_output_ids: list[str] = []
    while pending_output_ids:
        new_dg_and_wfe_rows = _get_data_generation_and_workflow_executions(db, pending_output_ids)
        dg_and_wfe_rows.update(new_dg_and_wfe_rows)
        visited_output_ids.extend(
            id_ for id_ in pending_output_ids if id_ not in visited_output_ids
        )
        input_ids = [
            input_id
            for row in new_dg_and_wfe_rows.values()
            for input_id in _document(row).get("has_input", [])
        ]
        pending_output_ids = list(
            dict.fromkeys(id_ for id_ in input_ids if id_ not in visited_output_ids)
        )

    workflow_rows = {
        id_: row
        for id_, row in dg_and_wfe_rows.items()
        if row.high_level_type == "nmdc:WorkflowExecution"
    }
    data_generation_rows = {
        id_: row
        for id_, row in dg_and_wfe_rows.items()
        if row.high_level_type == "nmdc:DataGeneration"
    }

    related_rows = [
        *data_object_rows.values(),
        *dg_and_wfe_rows.values(),
    ]
    biosample_ids = list(
        dict.fromkeys(biosample_id for row in related_rows for biosample_id in row.biosample_ids)
    )
    biosample_rows = _get_related_documents(db, biosample_ids)
    biosample_rows = {
        id_: row for id_, row in biosample_rows.items() if row.high_level_type == "nmdc:Biosample"
    }

    study_ids = list(
        dict.fromkeys(
            study_id
            for row in biosample_rows.values()
            for study_id in _document(row).get("associated_studies", [])
        )
    )
    study_rows = {}
    pending_study_ids = study_ids
    while pending_study_ids:
        new_rows = _get_related_documents(db, pending_study_ids)
        new_rows = {
            id_: row for id_, row in new_rows.items() if row.high_level_type == "nmdc:Study"
        }
        study_rows.update(new_rows)
        parent_ids = [
            parent_id
            for row in new_rows.values()
            for parent_id in (_document(row).get("part_of") or [])
        ]
        pending_study_ids = list(dict.fromkeys(id_ for id_ in parent_ids if id_ not in study_rows))

    graph = rocrate_dict["@graph"]
    for id_, row in sorted(study_rows.items()):
        parts = [
            biosample_id
            for biosample_id, biosample_row in biosample_rows.items()
            if id_ in _document(biosample_row).get("associated_studies", [])
        ]
        parts.extend(
            child_id
            for child_id, child_row in study_rows.items()
            if id_ in (_document(child_row).get("part_of") or [])
        )
        node = {"@id": id_, "@type": "nmdc:Study", "sameAs": f"{IDENTIFIER_PREFIX_URL}/{id_}"}
        if parts:
            node["hasPart"] = _references(parts)
        graph.append(node)
    for id_, row in sorted(biosample_rows.items()):
        node = {"@id": id_, "@type": "nmdc:Biosample", "sameAs": f"{IDENTIFIER_PREFIX_URL}/{id_}"}
        graph.append(node)
    for id_, row in sorted(data_generation_rows.items()):
        node = {
            "@id": id_,
            "@type": "nmdc:DataGeneration",
            "sameAs": f"{IDENTIFIER_PREFIX_URL}/{id_}",
        }
        related_biosamples = [id_ for id_ in row.biosample_ids if id_ in biosample_rows]
        if related_biosamples:
            node["object"] = _references(related_biosamples)
        workflows = [
            workflow_id
            for workflow_id, workflow_row in workflow_rows.items()
            if _overlap(
                _document(row).get("has_output", []),
                _document(workflow_row).get("has_input", []),
            )
        ]
        if workflows:
            node["result"] = _references(workflows)
        graph.append(node)
    for id_, row in sorted(workflow_rows.items()):
        workflow_type = _document(row).get("type", "nmdc:WorkflowExecution")
        node = {"@id": id_, "@type": workflow_type, "sameAs": f"{IDENTIFIER_PREFIX_URL}/{id_}"}
        related_biosamples = [id_ for id_ in row.biosample_ids if id_ in biosample_rows]
        if related_biosamples:
            node["object"] = _references(related_biosamples)
        graph.append(node)
    _add_archive_entities(
        graph,
        data_directory_entity,
        bulk_download,
        [*data_generation_rows, *workflow_rows],
    )
    return rocrate_dict
