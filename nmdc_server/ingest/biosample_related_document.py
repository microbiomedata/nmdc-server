from typing import List

from pymongo.database import Database
from sqlalchemy.orm import Session

from nmdc_server.models import BiosampleRelatedDocument


def get_downstream_related_documents(biosample_id: str, mongodb: Database) -> List[dict]:
    """
    Gets documents that are downstream of the specified `Biosample` and whose type ancestry chains
    include any of the following types (in this function, we call these "target types"):
    - nmdc:DataGeneration
    - nmdc:WorkflowExecution
    - nmdc:DataObject

    TODO: Use the source of truth collections instead of the derived `alldocs` collection,
          whose existence we want to keep as an "internal implementation detail of the Runtime."
          Using `alldocs` here (outside of the Runtime) is only for a temporary PoC.
    """
    projection = {"_id": 0}  # omits the `_id` field

    downstream_related_documents = []

    # Define a map from each target type to the name of the collection in which documents of that
    # type can reside.
    target_type_to_collection_name_map = {
        "nmdc:DataGeneration": "data_generation_set",
        "nmdc:WorkflowExecution": "workflow_execution_set",
        "nmdc:DataObject": "data_object_set",
    }
    target_types = list(target_type_to_collection_name_map.keys())

    # Get the downstream "sparse" documents that are of any target type. Note: The documents in the
    # `alldocs` collection are "sparse" in that they include only fields that are related to
    # identity (i.e. `id` and `_id`) plus some injected fields (i.e. `_upstream`, `_downstream`,
    # `_type_and_ancestors`).
    alldocs = mongodb.get_collection("alldocs")
    cursor = alldocs.aggregate(
        [
            # Focus on a single `Biosample`, rather than running every `Biosample` through the pipeline.
            {"$match": {"id": biosample_id}},
            # Recursively traverse downstream relationships to find all documents that are downstream
            # of that `Biosample` and have (directly or via their ancestry) any of the target types.
            {
                "$graphLookup": {
                    "from": "alldocs",
                    "startWith": "$id",
                    "connectFromField": "id",
                    "connectToField": "_upstream.id",
                    "as": "sparse_downstream_documents",
                    # Only traverse documents having any of the target types in their type ancestry.
                    "restrictSearchWithMatch": {"_type_and_ancestors": {"$in": target_types}},
                },
            },
            # Omit fields that are not NMDC Schema-compliant and that we will not be using below.
            {
                "$project": {
                    "sparse_downstream_documents._id": 0,
                    "sparse_downstream_documents._downstream": 0,
                    "sparse_downstream_documents._upstream": 0,
                }
            },
        ]
    )
    aggregation_pipeline_output = next(cursor, None)  # cursor will yield 0 or 1 results
    if aggregation_pipeline_output is None:
        sparse_downstream_documents = []
    else:
        sparse_downstream_documents = aggregation_pipeline_output.get(
            "sparse_downstream_documents",
            [],
        )

    # Get the "dense" (i.e. normal) counterparts of the "sparse" documents from the appropriate
    # collections and add them to the result.
    #
    # Note: If we refactor this to not use the `alldocs` collection, we may be able to get rid
    #       of this "hydration" step.
    #
    for sparse_downstream_document in sparse_downstream_documents:
        downstream_document_type_and_ancestors = sparse_downstream_document["_type_and_ancestors"]
        downstream_document_id = sparse_downstream_document["id"]

        # Identify the collection that contains the "dense" version of the "sparse" document.
        collection_name = None
        for target_type in target_types:
            if target_type in downstream_document_type_and_ancestors:
                collection_name = target_type_to_collection_name_map[target_type]
                break

        # Get the "dense" document from the identified collection.
        if collection_name is not None:
            document = mongodb.get_collection(collection_name).find_one(
                {"id": downstream_document_id},
                projection,
            )
            if document is not None:
                downstream_related_documents.append(document)
            else:
                raise ValueError(
                    f"Failed to find document '{downstream_document_id}' in '{collection_name}' collection"
                )
        else:
            raise ValueError(f"Invalid type ancestry: {downstream_document_type_and_ancestors}")

    return downstream_related_documents


def load(db: Session, mongodb: Database) -> None:
    """
    Retrieves `Biosample`-related documents from MongoDB and loads them into the Postgres database.
    Specifically, loads documents representing the `Biosample`, itself, its associated `Study`s,
    and its downstream `DataGeneration`s, `WorkflowExecution`s, and `DataObject`s.
    """
    biosample_set = mongodb.get_collection("biosample_set")
    study_set = mongodb.get_collection("study_set")
    projection = {"_id": 0}  # omits the `_id` field

    # Fetch documents from MongoDB
    for biosample_document in biosample_set.find({}, projection):
        documents_to_load = []

        # Include the `Biosample` document, itself.
        documents_to_load.append(biosample_document)

        # Include the associated `Study` document(s).
        associated_studies = biosample_document["associated_studies"]
        for study_document in study_set.find({"id": {"$in": associated_studies}}, projection):
            documents_to_load.append(study_document)

        # Include the downstream related documents (that are either `DataGeneration`s,
        # `WorkflowExecution`s, or `DataObject`s).
        biosample_id = biosample_document["id"]
        downstream_related_documents = get_downstream_related_documents(biosample_id, mongodb)
        documents_to_load.extend(downstream_related_documents)

        # Load the documents into the Postgres database.
        for document_to_load in documents_to_load:
            biosample_related_document = BiosampleRelatedDocument()
            biosample_related_document.biosample_id = biosample_id
            biosample_related_document.document = document_to_load
            db.add(biosample_related_document)
