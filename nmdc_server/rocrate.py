import json
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any, cast

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, union
from sqlalchemy.orm import Session

from nmdc_server import models
from nmdc_server.ingest.common import duration_logger
from nmdc_server.logger import get_logger
from nmdc_server.utils import safe_name

IDENTIFIER_PREFIX_URL = "https://bioregistry.io"


logger = get_logger(__name__)


def get_rocrate_base_bulk_download():
    """
    Base RO-Crate structure with placeholders for dynamic content.
    This gets included in bulk downloads as ro-crate-metadata.json.
    See https://www.researchobject.org/ro-crate/specification/1.2/introduction.html
    """
    return {
        "@context": [
            "https://w3id.org/ro/crate/1.2/context",
            {
                "nmdc": "https://w3id.org/nmdc/",
                "prov": "http://www.w3.org/ns/prov#",
            },
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
                        "description": "The query conditions used to select the data files included in this bulk download. Included here as stringified JSON.",
                        "value": "autogenerate-me",
                    },
                    {
                        "@type": "PropertyValue",
                        "name": "selected_file_types",
                        "description": "The file types selected for inclusion in this bulk download. Included here as stringified JSON.",
                        "value": "autogenerate-me",
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
    This describes the Manifest or DataGeneration directory and, when present,
    the WorkflowExecution directory level.
    We do this to minimize the RO-Crate size and because DataObject metadata is included in `metadata/data_objects.json`.
    """
    id_by_archive_name = {safe_name(id_): id_ for id_ in precise_entity_ids}
    directories: dict[str, dict[str, Any]] = {}

    for download_file in bulk_download.files:
        path = PurePosixPath(download_file.path)
        if len(path.parts) not in (3, 4) or path.parts[0] != "data":
            continue

        data_generation_or_manifest_name = path.parts[1]
        data_generation_dir_id = f"data/{data_generation_or_manifest_name}/"

        data_generation_dir_node = directories.setdefault(
            data_generation_dir_id,
            {"@id": data_generation_dir_id, "@type": "Dataset", "hasPart": []},
        )

        precise_data_generation_id = id_by_archive_name.get(data_generation_or_manifest_name)
        if precise_data_generation_id is not None:
            data_generation_dir_node["about"] = {"@id": precise_data_generation_id}

        data_generation_dir_reference = {"@id": data_generation_dir_id}
        if data_generation_dir_reference not in data_directory_entity.setdefault("hasPart", []):
            data_directory_entity["hasPart"].append(data_generation_dir_reference)

        if len(path.parts) == 3:
            continue

        workflow_execution_name = path.parts[2]
        workflow_execution_dir_id = f"{data_generation_dir_id}{workflow_execution_name}/"
        workflow_execution_dir_node = directories.setdefault(
            workflow_execution_dir_id,
            {"@id": workflow_execution_dir_id, "@type": "Dataset", "hasPart": []},
        )
        precise_workflow_execution_id = id_by_archive_name.get(workflow_execution_name)
        if precise_workflow_execution_id is not None:
            workflow_execution_dir_node["about"] = {"@id": precise_workflow_execution_id}

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
    """
    Returns documents representing all the `DataGeneration`s and `WorkflowExecution`s
    that directly outputted any of the specified `DataObject`s.
    """

    # If the caller didn't specify any `DataObject`s, return an empty dictionary. No need
    # to query the database.
    if len(output_ids) == 0:
        return dict()

    # Make a CTE (common table expression) that subsequent queries can treat as if
    # it were a table, without there actually being such a table in the database.
    # Docs: https://docs.sqlalchemy.org/en/13/core/tutorial.html#common-table-expressions-cte
    data_object_ids_cte = (
        select(models.DataObject.id.label("data_object_id"))
        .where(models.DataObject.id.in_(output_ids))
        .cte("relevant_data_object_ids")
    )

    # Make a SELECT statement that selects the ID of each `DataGeneration` that has
    # any of those `DataObject`s as one of its outputs.
    data_generation_output_association = models.omics_processing_output_association  # alias
    data_generation_ids_query = select(
        data_generation_output_association.c.omics_processing_id.label("id")
    ).join(
        data_object_ids_cte,
        data_generation_output_association.c.data_object_id
        == data_object_ids_cte.c.data_object_id,
    )

    # For each kind of `WorkflowExecution`, make a SELECT statement that selects
    # the ID of that kind of `WorkflowExecution` that has any of those `DataObject`s
    # as one of its outputs.
    workflow_execution_ids_queries = [
        select(workflow_execution_model.id.label("id"))
        .join(workflow_execution_model.outputs)
        .join(
            data_object_ids_cte,
            models.DataObject.id == data_object_ids_cte.c.data_object_id,
        )
        for workflow_execution_model in models.workflow_activity_types
    ]

    # Join all of those SELECT statements with UNION statements so that the one query
    # we eventually submit accounts for all of the above (i.e. `DataGeneration`s and
    # all kinds of  `WorkflowExecution`s. (Unlike UNION ALL, UNION omits duplicates.)
    # Docs: https://www.postgresql.org/docs/current/queries-union.html
    dgen_ids_and_wfe_ids_query = union(
        data_generation_ids_query, *workflow_execution_ids_queries
    )

    # Submit the query (composed of multiple SELECT queries UNION-ed together).
    #
    # Note: `db.execute()` returns a `Result` object made up of "rows", each of which has a single
    #       column whose value is the `DataObject` or `WorkflowExecution`'s `id` value. We use
    #       `.scalars().all()` and an outer `list()` to convert it into a list of those values.
    #
    dgen_ids_and_wfe_ids_query_result = db.execute(dgen_ids_and_wfe_ids_query)
    dgen_ids_and_wfe_ids: list[str] = list(dgen_ids_and_wfe_ids_query_result.scalars().all())

    # Finally, use those `DataGeneration` and `WorkflowExecution` IDs to get the corresponding
    # documents from the `biosample_related_document` table.
    data_generations_and_workflow_executions = _get_related_documents(db, dgen_ids_and_wfe_ids)
    return data_generations_and_workflow_executions


def _get_manifest_members(db: Session, data_generation_ids: list[str]) -> dict[str, list[str]]:
    """Group the specified DataGenerations by their Manifest IDs."""
    rows = db.execute(
        select(
            models.OmicsProcessing.id,  # type: ignore[arg-type]
            models.OmicsProcessing.poolable_replicates_manifest_id,
        ).where(models.OmicsProcessing.id.in_(data_generation_ids))
    )
    members: dict[str, list[str]] = {}
    for data_generation_id, manifest_id in rows:
        if manifest_id is not None and manifest_id != data_generation_id:
            members.setdefault(manifest_id, []).append(data_generation_id)
    return {manifest_id: sorted(members[manifest_id]) for manifest_id in sorted(members)}


def _get_archived_workflows_by_data_generation(
    bulk_download: models.BulkDownload,
    data_generation_ids: list[str],
) -> dict[str, list[str]]:
    """Group archived WorkflowExecutions by their informing DataGenerations."""
    associated_data_generation_ids = set(data_generation_ids)
    workflows: dict[str, list[str]] = {}
    for download_file in bulk_download.files:
        workflow = download_file.data_object.was_generated_by
        if workflow is None or isinstance(workflow, models.OmicsProcessing):
            continue
        for data_generation in workflow.was_informed_by:
            if data_generation.id in associated_data_generation_ids:
                workflows.setdefault(data_generation.id, []).append(workflow.id)
    return {
        data_generation_id: sorted(dict.fromkeys(workflows[data_generation_id]))
        for data_generation_id in sorted(workflows)
    }


def generate_rocrate_for_bulk_download(  # noqa: C901
    db: Session, bulk_download: models.BulkDownload, data_object_ids: list[str]
):
    """Generates an RO-Crate metadata object for a given bulk download record."""
    rocrate_dict = get_rocrate_base_bulk_download()
    root_data_entity = get_root_data_entity(rocrate_dict)
    if not root_data_entity:
        raise ValueError("RO-Crate structure is missing the root data entity with @id './'")
    root_data_entity["datePublished"] = bulk_download.created.isoformat()
    now = datetime.now(timezone.utc)
    root_data_entity["description"] = (
        f"Bulk download of data files from the NMDC Data Portal, generated on {now.strftime("%Y-%m-%d")} at {now.strftime('%H:%M:%S%z')}. The files included in the data directory are determined by the `query_conditions` and `selected_file_types` specified for this bulk download."
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
    query_conditions_property["value"] = json.dumps(jsonable_encoder(bulk_download.conditions))
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
    selected_file_types_property["value"] = json.dumps(jsonable_encoder(bulk_download.filter))
    data_directory_entity = next(
        (item for item in rocrate_dict["@graph"] if item["@id"] == "data/"), None
    )
    if not data_directory_entity:
        raise ValueError("RO-Crate structure is missing the data directory entity with @id 'data/'")
    data_directory_entity["description"] = (
        f"Directory containing the {len(data_object_ids)} data {"file" if len(data_object_ids) == 1 else "files"} for this bulk download. "
        "Files are organized by DataGeneration and WorkflowExecution."
    )

    data_object_rows = _get_related_documents(db, list(dict.fromkeys(data_object_ids)))
    dg_and_wfe_rows: dict[str, models.BiosampleRelatedDocument] = {}
    pending_output_ids = list(dict.fromkeys(data_object_ids))
    visited_output_ids: list[str] = []
    while pending_output_ids:
        # TODO: Remove this `duration_logger` context once we've fixed the performance problems.
        with duration_logger(logger=logger, task_name="Get DGENs and WFEs", precision=1):
            new_dg_and_wfe_rows = _get_data_generation_and_workflow_executions(
                db, pending_output_ids
            )
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

    discovered_workflow_rows = {
        id_: row
        for id_, row in dg_and_wfe_rows.items()
        if row.high_level_type == "nmdc:WorkflowExecution"
    }
    data_generation_rows = {
        id_: row
        for id_, row in dg_and_wfe_rows.items()
        if row.high_level_type == "nmdc:DataGeneration"
    }
    manifest_members = _get_manifest_members(db, list(data_generation_rows))
    archived_workflows_by_data_generation = _get_archived_workflows_by_data_generation(
        bulk_download, list(data_generation_rows)
    )
    archived_workflow_ids = {
        workflow_id
        for workflow_ids in archived_workflows_by_data_generation.values()
        for workflow_id in workflow_ids
    }
    # The recursive lookup above follows inputs back to their DataGeneration. It can
    # encounter upstream WorkflowExecutions along the way, but those executions do
    # not describe anything included in this archive. Only emit workflow nodes for
    # executions that actually generated one of the downloaded files.
    workflow_rows = {
        id_: row for id_, row in discovered_workflow_rows.items() if id_ in archived_workflow_ids
    }
    informing_data_generations_by_workflow: dict[str, list[str]] = {}
    for data_generation_id, workflow_ids in archived_workflows_by_data_generation.items():
        for workflow_id in workflow_ids:
            informing_data_generations_by_workflow.setdefault(workflow_id, []).append(
                data_generation_id
            )

    related_rows = [
        *data_object_rows.values(),
        *data_generation_rows.values(),
        *workflow_rows.values(),
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
    _add_archive_entities(
        graph,
        data_directory_entity,
        bulk_download,
        [*manifest_members, *data_generation_rows, *workflow_rows],
    )
    for id_, member_ids in manifest_members.items():
        graph.append(
            {
                "@id": id_,
                "@type": "nmdc:Manifest",
                "sameAs": f"{IDENTIFIER_PREFIX_URL}/{id_}",
                "hasPart": _references(member_ids),
            }
        )
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
            node["prov:used"] = _references(related_biosamples)
        graph.append(node)
    for id_, row in sorted(workflow_rows.items()):
        workflow_type = _document(row).get("type", "nmdc:WorkflowExecution")
        node = {"@id": id_, "@type": workflow_type, "sameAs": f"{IDENTIFIER_PREFIX_URL}/{id_}"}
        informing_data_generations = informing_data_generations_by_workflow.get(id_, [])
        if informing_data_generations:
            node["prov:wasInformedBy"] = _references(informing_data_generations)
        graph.append(node)
    return rocrate_dict
