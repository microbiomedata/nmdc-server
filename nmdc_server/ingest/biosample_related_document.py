from typing import List

from pymongo.database import Database
from sqlalchemy import func, text, update
from sqlalchemy.orm import Session

from nmdc_server.ingest.common import duration_logger
from nmdc_server.logger import get_logger
from nmdc_server.models import BiosampleRelatedDocument


def load(db: Session, mongodb: Database) -> None:
    r"""
    Reads all documents from the following MongoDB collections (listed below); then, for each
    document, determines the IDs its downstream neighbor(s), determines the IDs of the biosample(s)
    the document is associated with, and writes the document (without its `_id` field), the IDs of
    its downstream neighbors, and the IDs of the associated biosample(s) to the Postgres database.

    The MongoDB collections are:
    - `biosample_set`
    - `study_set`
    - `data_generation_set`
    - `workflow_execution_set`
    - `data_object_set`
    """

    logger = get_logger(__name__)

    # Read the documents (omitting their `_id` fields) from the MongoDB database
    # and store them in the Postgres database.
    projection_omitting_oid = {"_id": 0}
    projection_selecting_id = {"_id": 0, "id": 1}

    biosample_set = mongodb.get_collection("biosample_set")
    study_set = mongodb.get_collection("study_set")
    data_generation_set = mongodb.get_collection("data_generation_set")
    workflow_execution_set = mongodb.get_collection("workflow_execution_set")
    data_object_set = mongodb.get_collection("data_object_set")

    with duration_logger(logger, "Loading biosamples and identifying downstream neighbors"):
        for biosample_document in biosample_set.find({}, projection_omitting_oid):
            biosample_related_document = BiosampleRelatedDocument()
            biosample_related_document.biosample_ids = [biosample_document["id"]]
            biosample_related_document.high_level_type = "nmdc:Biosample"
            biosample_related_document.document = biosample_document

            # Identify downstream neighbors.
            biosample_related_document.downstream_neighbor_ids = []
            for data_generation_document in data_generation_set.find(
                {"has_input": biosample_document["id"]}, projection_selecting_id
            ):
                biosample_related_document.downstream_neighbor_ids.append(
                    data_generation_document["id"]
                )

            db.add(biosample_related_document)
        db.commit()

    with duration_logger(
        logger, "Loading studies and identifying downstream neighbors (and related biosamples)"
    ):
        for study_document in study_set.find({}, projection_omitting_oid):
            biosample_related_document = BiosampleRelatedDocument()
            biosample_related_document.biosample_ids = []
            biosample_related_document.high_level_type = "nmdc:Study"
            biosample_related_document.document = study_document

            # Identify downstream neighbors.
            biosample_related_document.downstream_neighbor_ids = []
            for biosample_document in biosample_set.find(
                {"associated_studies": study_document["id"]}, projection_selecting_id
            ):
                biosample_related_document.downstream_neighbor_ids.append(biosample_document["id"])

                # In this case, we also record this downstream neighbor as a related biosample,
                # specifically, since we want to identify those anyway for each document.
                biosample_related_document.biosample_ids.append(biosample_document["id"])

            db.add(biosample_related_document)
        db.commit()

    with duration_logger(logger, "Loading data generations and identifying downstream neighbors"):
        for data_generation_document in data_generation_set.find({}, projection_omitting_oid):
            biosample_related_document = BiosampleRelatedDocument()
            biosample_related_document.biosample_ids = []
            biosample_related_document.high_level_type = "nmdc:DataGeneration"
            biosample_related_document.document = data_generation_document

            # Identify downstream neighbors.
            biosample_related_document.downstream_neighbor_ids = []
            if "has_output" in data_generation_document:
                biosample_related_document.downstream_neighbor_ids = data_generation_document[
                    "has_output"
                ]

            db.add(biosample_related_document)
        db.commit()

    with duration_logger(
        logger, "Loading workflow executions and identifying downstream neighbors"
    ):
        for workflow_execution_document in workflow_execution_set.find({}, projection_omitting_oid):
            biosample_related_document = BiosampleRelatedDocument()
            biosample_related_document.biosample_ids = []
            biosample_related_document.high_level_type = "nmdc:WorkflowExecution"
            biosample_related_document.document = workflow_execution_document

            # Identify downstream neighbors.
            biosample_related_document.downstream_neighbor_ids = []
            if "has_output" in workflow_execution_document:
                biosample_related_document.downstream_neighbor_ids = workflow_execution_document[
                    "has_output"
                ]

            db.add(biosample_related_document)
        db.commit()

    with duration_logger(logger, "Loading data objects and identifying downstream neighbors"):
        for data_object_document in data_object_set.find({}, projection_omitting_oid):
            biosample_related_document = BiosampleRelatedDocument()
            biosample_related_document.biosample_ids = []
            biosample_related_document.high_level_type = "nmdc:DataObject"
            biosample_related_document.document = data_object_document

            # Identify downstream neighbors.
            biosample_related_document.downstream_neighbor_ids = []
            for workflow_execution_document in workflow_execution_set.find(
                {"has_input": data_object_document["id"]}, projection_selecting_id
            ):
                biosample_related_document.downstream_neighbor_ids.append(
                    workflow_execution_document["id"]
                )

            db.add(biosample_related_document)
        db.commit()

    # Use the downstream neighbor identities we gathered above to determine which biosample(s)
    # each document is associated with.
    with duration_logger(logger, "Populating `biosample_ids` fields."):
        # Get the IDs of all biosamples.
        biosample_ids = [
            row[0]
            for row in db.query(
                BiosampleRelatedDocument.document["id"].astext,
            )
            .filter(BiosampleRelatedDocument.high_level_type == "nmdc:Biosample")
            .all()
        ]
        # For each biosample ID, identify each document that is _anywhere_ downstream from that biosample.
        for biosample_id in biosample_ids:
            query = """--sql
                -- Note: This "WITH" statement is a Common Table Expression (CTE), which creates a
                --       temporary table that we can use for a single query. We use it to recursively
                --       traverse downstream neighbor relationships beginning from a single biosample.
                --
                -- Docs: https://www.postgresql.org/docs/current/queries-with.html#QUERIES-WITH-RECURSIVE
                --
                WITH RECURSIVE temp_table AS (
                    -- ▶️ Base case: Get the immediate downstream neighbors of the specified biosample.
                    --               We could have gotten those IDs outside of this query, but doing it
                    --               here keeps this base case more symmetrical with the recursive case.
                    --
                    -- Note: `unnest()` expands an array into a set of rows, where each array element
                    --       is on its own row. We use it here to expand the `downstream_neighbor_ids`
                    --       array elements into individual rows so that we can join on each of them.
                    --       Docs: https://www.postgresql.org/docs/current/functions-array.html
                    --
                    -- Note: `:biosample_id` is a reference to a query parameter having that name.
                    --
                    SELECT unnest(downstream_neighbor_ids) AS downstream_document_id
                    FROM biosample_related_document
                    WHERE document->>'id' = :biosample_id

                    UNION ALL

                    -- 🔁 Recursive case: Get the downstream neighbors of the documents identified
                    --                    in the previous iteration.
                    --
                    -- ⏹️ Exit condition: When there are no downstream neighbors, the `SELECT` will
                    --                    return an empty set, which causes recursion to end.
                    --
                    SELECT unnest(current_document.downstream_neighbor_ids) AS downstream_document_id
                    FROM temp_table AS previous_temp_table, biosample_related_document AS current_document
                    WHERE current_document.document->>'id' = previous_temp_table.downstream_document_id
                )

                -- Return the distinct IDs of all the documents that are downstream from the biosample.
                SELECT DISTINCT downstream_document_id FROM temp_table;
            """
            rows = db.execute(text(query), {"biosample_id": biosample_id}).fetchall()
            downstream_document_ids: List[str] = [row[0] for row in rows]
            logger.debug(
                f"Biosample {biosample_id} downstream documents: {downstream_document_ids}"
            )

            # Update each document that is _anywhere_ downstream from this biosample, so that its
            # `biosample_ids` column contains the ID of this biosample.
            downstream_documents = (
                db.query(BiosampleRelatedDocument)
                .filter(BiosampleRelatedDocument.document["id"].astext.in_(downstream_document_ids))
                .all()
            )
            for downstream_document in downstream_documents:
                if biosample_id not in downstream_document.biosample_ids:
                    downstream_document.biosample_ids.append(biosample_id)

    return None
