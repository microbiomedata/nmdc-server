from typing import List

from pymongo.collection import Collection
from pymongo.database import Database
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from nmdc_server.ingest.common import duration_logger
from nmdc_server.logger import get_logger
from nmdc_server.models import BiosampleRelatedDocument

# Define some reusable MongoDB projections.
projection_omitting_oid = {"_id": 0}
projection_selecting_id = {"_id": 0, "id": 1}


def dedupe(ids: List[str]) -> List[str]:
    """
    Returns the specified list after deleting any redundant values from it.

    >>> dedupe([1, 2, 3, 2])
    [1, 2, 3]
    >>> dedupe([])
    []
    """
    return list(set(ids))


def invert_dict_of_lists(dict_of_lists: dict[str, List[str]]) -> dict[str, List[str]]:
    """
    Inverts a dictionary whose values are lists; so that the keys of the returned dictionary are
    the distinct elements of those lists, and the values are lists of the keys from the original
    dictionary that had that element in their values.

    >>> invert_dict_of_lists({"a": ["1", "2"], "b": ["2", "3"], "c": []})
    {'1': ['a'], '2': ['a', 'b'], '3': ['b']}
    >>> invert_dict_of_lists({"a": ["1", "1"]})  # test: omits duplicates
    {'1': ['a']}
    >>> invert_dict_of_lists({})
    {}
    """

    inverted_dict: dict[str, List[str]] = {}
    for string_key, string_values in dict_of_lists.items():
        for string_value in string_values:
            if string_value not in inverted_dict.keys():  # initializes list
                inverted_dict[string_value] = []
            if string_key not in inverted_dict[string_value]:  # omits duplicate values
                inverted_dict[string_value].append(string_key)

    return inverted_dict


def load_biosamples(
    db: Session,
    biosample_set: Collection,
    data_generation_ids_by_input_id: dict[str, List[str]],
    material_processing_ids_by_input_id: dict[str, List[str]],
) -> tuple[list[str], dict[str, list[str]]]:
    """
    Reads each document from the `biosample_set` MongoDB collection, identifies its [immediate]
    downstream neighbors, and creates a `BiosampleRelatedDocument` row (in the Postgres session)
    that represents that document. The row will have its `biosample_ids` column initialized to
    an array consisting of the ID of the biosample whose document is on that row.

    Returns a tuple, whose first item is a list of all biosample IDs and whose second item is
    a dictionary mapping the `id` of each `Biosample` that has any associated studies, to its
    `associated_studies` value.
    """

    biosample_ids = []
    biosample_associated_studies_values = {}

    for biosample_document in biosample_set.find({}, projection_omitting_oid):
        biosample_related_document = BiosampleRelatedDocument()
        biosample_related_document.id = biosample_document["id"]
        biosample_related_document.biosample_ids = [biosample_document["id"]]
        biosample_related_document.high_level_type = "nmdc:Biosample"
        biosample_related_document.document = biosample_document

        # Identify downstream neighbors.
        #
        # Note: Instead of querying the `data_generation_set` and `material_processing_set`
        #       MongoDB collections here, we take advantage of the look-up tables passed in.
        #
        biosample_related_document.downstream_neighbor_ids = []
        if biosample_document["id"] in data_generation_ids_by_input_id:
            biosample_related_document.downstream_neighbor_ids.extend(
                data_generation_ids_by_input_id[biosample_document["id"]]
            )
        if biosample_document["id"] in material_processing_ids_by_input_id:
            biosample_related_document.downstream_neighbor_ids.extend(
                material_processing_ids_by_input_id[biosample_document["id"]]
            )

        biosample_related_document.downstream_neighbor_ids = dedupe(
            biosample_related_document.downstream_neighbor_ids
        )

        # Add the biosample's ID to the list we will return.
        biosample_ids.append(biosample_document["id"])

        # Store its "associated_studies" value in the dictionary we will return.
        if "associated_studies" in biosample_document:
            associated_studies = biosample_document["associated_studies"]
            if not isinstance(associated_studies, list):
                raise ValueError(f"Value is not schema-compliant: {associated_studies=}")
            biosample_associated_studies_values[biosample_document["id"]] = associated_studies

        db.add(biosample_related_document)

    return biosample_ids, biosample_associated_studies_values


def load_studies(
    db: Session,
    study_set: Collection,
    biosample_ids_by_associated_study_id: dict[str, list[str]],
) -> None:
    """
    Reads each document from the `study_set` MongoDB collection, identifies its [immediate]
    downstream neighbors, and creates a `BiosampleRelatedDocument` row (in the Postgres session)
    that represents that document.

    Also identifies the biosample(s) associated with each study, since it's so readily accessible.
    """

    for study_document in study_set.find({}, projection_omitting_oid):
        biosample_related_document = BiosampleRelatedDocument()
        biosample_related_document.id = study_document["id"]
        biosample_related_document.biosample_ids = []
        biosample_related_document.high_level_type = "nmdc:Study"
        biosample_related_document.document = study_document

        # Identify downstream neighbors.
        #
        # Note: Instead of querying the `biosample_set` MongoDB collection here,
        #       we take advantage of the look-up tables passed in.
        #
        biosample_related_document.downstream_neighbor_ids = []
        if study_document["id"] in biosample_ids_by_associated_study_id:
            biosample_ids = biosample_ids_by_associated_study_id[study_document["id"]]
            biosample_related_document.downstream_neighbor_ids.extend(biosample_ids)

            # Also store the biosamples' `id`s as related biosample `id`s; given that our
            # later step of traversing the schema will only go _downstream_ (not upstream)
            # of biosamples (whereas studies are _upstream_ of biosamples).
            biosample_related_document.biosample_ids.extend(biosample_ids)

        biosample_related_document.downstream_neighbor_ids = dedupe(
            biosample_related_document.downstream_neighbor_ids
        )
        biosample_related_document.biosample_ids = dedupe(biosample_related_document.biosample_ids)

        db.add(biosample_related_document)


def load_data_generations(
    db: Session,
    data_generation_set: Collection,
    workflow_execution_ids_by_informant_id: dict[str, List[str]],
) -> dict[str, list[str]]:
    """
    Reads each document from the `data_generation_set` MongoDB collection, identifies its
    [immediate] downstream neighbors, and creates a `BiosampleRelatedDocument` row (in the Postgres
    session) that represents that document.

    Returns a dictionary mapping the `id` of each `DataGeneration` that has any any inputs,
    to its `has_input` value.
    """

    data_generation_has_input_values = {}

    for data_generation_document in data_generation_set.find({}, projection_omitting_oid):
        biosample_related_document = BiosampleRelatedDocument()
        biosample_related_document.id = data_generation_document["id"]
        biosample_related_document.biosample_ids = []
        biosample_related_document.high_level_type = "nmdc:DataGeneration"
        biosample_related_document.document = data_generation_document

        # Identify downstream neighbors.
        biosample_related_document.downstream_neighbor_ids = []
        if "has_output" in data_generation_document:
            biosample_related_document.downstream_neighbor_ids.extend(
                data_generation_document["has_output"]
            )
        if "generates_calibration" in data_generation_document:
            biosample_related_document.downstream_neighbor_ids.append(
                data_generation_document["generates_calibration"]
            )
        # Note: Instead of querying the `workflow_execution_set` MongoDB collection here,
        #       we take advantage of the look-up table passed in.
        if data_generation_document["id"] in workflow_execution_ids_by_informant_id:
            biosample_related_document.downstream_neighbor_ids.extend(
                workflow_execution_ids_by_informant_id[data_generation_document["id"]]
            )

        biosample_related_document.downstream_neighbor_ids = dedupe(
            biosample_related_document.downstream_neighbor_ids
        )

        db.add(biosample_related_document)

        # Store its "has_input" value in the dictionary we will return.
        if "has_input" in data_generation_document:
            has_input = data_generation_document["has_input"]
            if not isinstance(has_input, list):
                raise ValueError(f"Value is not schema-compliant: {has_input=}")
            data_generation_has_input_values[data_generation_document["id"]] = has_input

    return data_generation_has_input_values


def load_calibrations(
    db: Session,
    calibration_set: Collection,
) -> None:
    """
    Reads each document from the `calibration_set` MongoDB collection, identifies its
    [immediate] downstream neighbors, and creates a `BiosampleRelatedDocument` row (in the Postgres
    session) that represents that document.

    Reference: https://microbiomedata.github.io/nmdc-schema/CalibrationInformation/
    """

    for calibration_document in calibration_set.find({}, projection_omitting_oid):
        biosample_related_document = BiosampleRelatedDocument()
        biosample_related_document.id = calibration_document["id"]
        biosample_related_document.biosample_ids = []
        biosample_related_document.high_level_type = "nmdc:CalibrationInformation"
        biosample_related_document.document = calibration_document

        # Identify downstream neighbors.
        biosample_related_document.downstream_neighbor_ids = []
        if "calibration_object" in calibration_document:
            biosample_related_document.downstream_neighbor_ids.append(
                calibration_document["calibration_object"]
            )

        biosample_related_document.downstream_neighbor_ids = dedupe(
            biosample_related_document.downstream_neighbor_ids
        )

        db.add(biosample_related_document)


def load_material_processings(
    db: Session,
    material_processing_set: Collection,
) -> dict[str, list[str]]:
    """
    Reads each document from the `material_processing_set` MongoDB collection, identifies its
    [immediate] downstream neighbors, and creates a `BiosampleRelatedDocument` row (in the Postgres
    session) that represents that document.

    Returns a dictionary mapping the `id` of each `MaterialProcessing` that has any any inputs,
    to its `has_input` value.
    """

    material_processing_has_input_values = {}

    for material_processing_document in material_processing_set.find({}, projection_omitting_oid):
        biosample_related_document = BiosampleRelatedDocument()
        biosample_related_document.id = material_processing_document["id"]
        biosample_related_document.biosample_ids = []
        biosample_related_document.high_level_type = "nmdc:MaterialProcessing"
        biosample_related_document.document = material_processing_document

        # Identify downstream neighbors.
        biosample_related_document.downstream_neighbor_ids = []
        if "has_output" in material_processing_document:
            biosample_related_document.downstream_neighbor_ids.extend(
                material_processing_document["has_output"]
            )

        biosample_related_document.downstream_neighbor_ids = dedupe(
            biosample_related_document.downstream_neighbor_ids
        )

        db.add(biosample_related_document)

        # Store its "has_input" value in the dictionary we will return.
        if "has_input" in material_processing_document:
            has_input = material_processing_document["has_input"]
            if not isinstance(has_input, list):
                raise ValueError(f"Value is not schema-compliant: {has_input=}")
            material_processing_has_input_values[material_processing_document["id"]] = has_input

    return material_processing_has_input_values


def load_processed_samples(
    db: Session,
    processed_sample_set: Collection,
    data_generation_ids_by_input_id: dict[str, List[str]],
    material_processing_ids_by_input_id: dict[str, List[str]],
) -> None:
    """
    Reads each document from the `processed_sample_set` MongoDB collection, identifies its
    [immediate] downstream neighbors, and creates a `BiosampleRelatedDocument` row (in the Postgres
    session) that represents that document.
    """

    for processed_sample_document in processed_sample_set.find({}, projection_omitting_oid):
        biosample_related_document = BiosampleRelatedDocument()
        biosample_related_document.id = processed_sample_document["id"]
        biosample_related_document.biosample_ids = []
        biosample_related_document.high_level_type = "nmdc:ProcessedSample"
        biosample_related_document.document = processed_sample_document

        # Identify downstream neighbors.
        #
        # Note: Instead of querying the `data_generation_set` and `material_processing_set`
        #       MongoDB collections here, we take advantage of the look-up tables passed in.
        #
        biosample_related_document.downstream_neighbor_ids = []
        if processed_sample_document["id"] in data_generation_ids_by_input_id:
            biosample_related_document.downstream_neighbor_ids.extend(
                data_generation_ids_by_input_id[processed_sample_document["id"]]
            )
        if processed_sample_document["id"] in material_processing_ids_by_input_id:
            biosample_related_document.downstream_neighbor_ids.extend(
                material_processing_ids_by_input_id[processed_sample_document["id"]]
            )

        biosample_related_document.downstream_neighbor_ids = dedupe(
            biosample_related_document.downstream_neighbor_ids
        )

        db.add(biosample_related_document)


def load_workflow_executions(
    db: Session,
    workflow_execution_set: Collection,
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """
    Reads each document from the `workflow_execution_set` MongoDB collection, identifies its
    [immediate] downstream neighbors, and creates a `BiosampleRelatedDocument` row (in the Postgres
    session) that represents that document.
    """

    workflow_execution_has_input_values = {}
    workflow_execution_was_informed_by_values = {}

    for workflow_execution_document in workflow_execution_set.find({}, projection_omitting_oid):
        biosample_related_document = BiosampleRelatedDocument()
        biosample_related_document.id = workflow_execution_document["id"]
        biosample_related_document.biosample_ids = []
        biosample_related_document.high_level_type = "nmdc:WorkflowExecution"
        biosample_related_document.document = workflow_execution_document

        # Identify downstream neighbors.
        biosample_related_document.downstream_neighbor_ids = []
        if "has_output" in workflow_execution_document:
            biosample_related_document.downstream_neighbor_ids.extend(
                workflow_execution_document["has_output"]
            )

        # TODO: The Runtime currently designates the `uses_calibration` slot as "downstream-facing"
        #       (although "upstream-facing" seems more intuitive to me). Since we are trying to
        #       mimic the behavior of the Runtime's "linked instances" endpoint here, we'll treat it
        #       as "downstream-facing" here also.
        #
        #       Keep an eye on the following GitHub Issue, which is about the slot's "direction":
        #       https://github.com/microbiomedata/nmdc-runtime/issues/1400
        #
        #       Reference: https://microbiomedata.github.io/nmdc-schema/uses_calibration/
        #
        if "uses_calibration" in workflow_execution_document:
            biosample_related_document.downstream_neighbor_ids.extend(
                workflow_execution_document["uses_calibration"]
            )

        biosample_related_document.downstream_neighbor_ids = dedupe(
            biosample_related_document.downstream_neighbor_ids
        )

        db.add(biosample_related_document)

        # Store its "has_input" value in the dictionary we will return.
        if "has_input" in workflow_execution_document:
            has_input = workflow_execution_document["has_input"]
            if not isinstance(has_input, list):
                raise ValueError(f"Value is not schema-compliant: {has_input=}")
            workflow_execution_has_input_values[workflow_execution_document["id"]] = has_input

        # Store its "was_informed_by" value in the dictionary we will return.
        if "was_informed_by" in workflow_execution_document:
            was_informed_by = workflow_execution_document["was_informed_by"]
            if not isinstance(was_informed_by, list):
                raise ValueError(f"Value is not schema-compliant: {was_informed_by=}")
            workflow_execution_was_informed_by_values[workflow_execution_document["id"]] = (
                was_informed_by
            )

    return workflow_execution_has_input_values, workflow_execution_was_informed_by_values


def load_data_objects(
    db: Session,
    data_object_set: Collection,
    workflow_execution_ids_by_input_id: dict[str, List[str]],
) -> dict[str, str]:
    """
    Reads each document from the `data_object_set` MongoDB collection, identifies its
    [immediate] downstream neighbors, and creates a `BiosampleRelatedDocument` row (in the Postgres
    session) that represents that document.

    Returns a dictionary where each item's key is the `id` value of a `DataObject` document that has
    a `was_generated_by` field, and each item's value is the value of that `was_generated_by` field.

    Note: According to the NMDC Schema, the range of `was_generated_by` is the `id` of an instance
          of `DataEmitterProcess`, the (abstract) parent class of `DataGeneration` and
          `WorkflowExecution`.
    """

    data_object_was_generated_by_values = {}

    for data_object_document in data_object_set.find({}, projection_omitting_oid):
        biosample_related_document = BiosampleRelatedDocument()
        biosample_related_document.id = data_object_document["id"]
        biosample_related_document.biosample_ids = []
        biosample_related_document.high_level_type = "nmdc:DataObject"
        biosample_related_document.document = data_object_document

        # Identify downstream neighbors.
        #
        # Note: Instead of querying the `workflow_execution_set` MongoDB collection here,
        #       we take advantage of the look-up tables passed in.
        #
        biosample_related_document.downstream_neighbor_ids = []
        if data_object_document["id"] in workflow_execution_ids_by_input_id:
            biosample_related_document.downstream_neighbor_ids.extend(
                workflow_execution_ids_by_input_id[data_object_document["id"]]
            )

        biosample_related_document.downstream_neighbor_ids = dedupe(
            biosample_related_document.downstream_neighbor_ids
        )

        db.add(biosample_related_document)

        # Store its "was_generated_by" value in the dictionary we will return.
        if "was_generated_by" in data_object_document:
            was_generated_by = data_object_document["was_generated_by"]
            if not isinstance(was_generated_by, str):
                raise ValueError(f"Value is not schema-compliant: {was_generated_by=}")
            data_object_was_generated_by_values[data_object_document["id"]] = was_generated_by

    return data_object_was_generated_by_values


def backfill_downstream_neighbor_lists_of_data_emitter_processes(
    db: Session,
    generated_data_object_ids_by_data_emitter_process_id: dict[str, List[str]],
) -> None:
    """
    Updates existing rows containing documents representing `DataEmitterProcess` documents,
    so that those rows' `downstream_neighbor_ids` account for the relationships described
    by the dictionary passed in, which was derived from `was_generated_by` relationships.

    Note: `DataEmitterProcess` is the (abstract) parent class of `DataGeneration` and `WorkflowExecution`.
    """

    # Update existing rows containing documents representing `DataEmitterProcess` documents,
    # so that those rows' `downstream_neighbor_ids` account for the relationships described by
    # the dictionary passed in.
    #
    # TODO: We have a performance optimization opportunity here. Instead of issuing one query per
    #       `DataEmitterProcess` (i.e. per key in the dictionary), we could issue a single query
    #       that retrieves all of the relevant rows at once, and then update their
    #       `downstream_neighbor_ids` in Python, and then commit all the updated rows at once.
    #
    for (
        data_emitter_process_id,
        generated_data_object_ids,
    ) in generated_data_object_ids_by_data_emitter_process_id.items():
        if not generated_data_object_ids:
            continue

        biosample_related_document = (
            db.query(BiosampleRelatedDocument)
            .filter(BiosampleRelatedDocument.id == data_emitter_process_id)
            .one_or_none()
        )
        if biosample_related_document is None:
            continue

        existing_downstream_neighbor_ids = biosample_related_document.downstream_neighbor_ids or []
        biosample_related_document.downstream_neighbor_ids = dedupe(
            existing_downstream_neighbor_ids + generated_data_object_ids
        )


def populate_biosample_ids_column(db: Session, biosample_ids: List[str]) -> None:
    """
    Identifies the IDs of all relevant documents that are downstream from each biosample (whose ID
    is passed in), and then updates the `biosample_ids` column (in the Postgres session) of each
    downstream document's row so that it contains the ID of that [upstream] biosample.

    This involves a recursive Postgres query. We included extensive commentary within the query in
    an attempt to facilitate maintaining the query over time.
    """

    # For each biosample ID, identify each document that is _anywhere_ downstream from that biosample.
    for biosample_id in biosample_ids:
        query = """--sql
            -- Note: This "WITH RECURSIVE" statement creates a temporary so-called "working table"
            --       (which happens to have a single column, named `downstream_neighbor_id`)
            --       that we can reference from within the "recursive term" of the same query.
            --       We use this query to recursively traverse downstream neighbors, relative to
            --       one specific biosample (whose ID is referenced by `:biosample_id` below).
            --
            -- Docs: https://www.postgresql.org/docs/current/queries-with.html#QUERIES-WITH-RECURSIVE
            --
            WITH RECURSIVE working_table(downstream_neighbor_id) AS (
                    -- 1️⃣ Non-recursive term: Get the IDs of the (immediate) downstream neighbors
                    --                        of the specified biosample. We could have gotten
                    --                        those IDs outside of this query, but doing it here
                    --                        keeps this "non-recursive term" more conceptually
                    --                        symmetrical with the "recursive term" below.
                    --
                    -- Note: `unnest()` expands an array into a set of rows, where each array
                    --       element is on its own row. We use it here to expand the
                    --       `downstream_neighbor_ids` array elements into individual rows so
                    --       that we can then "join" on each of them.
                    --
                    -- Docs: https://www.postgresql.org/docs/current/functions-array.html
                    --
                    SELECT unnest(brd.downstream_neighbor_ids) AS downstream_neighbor_id
                    FROM biosample_related_document AS brd
                    WHERE brd.id = :biosample_id
                UNION
                    -- 🔁 Recursive term: Get the IDs of the (immediate) downstream neighbors of
                    --                    the documents identified in the previous iteration.
                    --                    Once there are no such IDs, this will return no rows,
                    --                    causing recursion [down that specific path] to end.
                    --
                    SELECT unnest(brd_2.downstream_neighbor_ids) AS downstream_neighbor_id
                    FROM biosample_related_document AS brd_2,
                         working_table
                    WHERE brd_2.id = working_table.downstream_neighbor_id
            )

            -- Return the distinct IDs of all the documents that are downstream from the biosample.
            SELECT DISTINCT downstream_neighbor_id FROM working_table;
        """
        rows = db.execute(text(query), {"biosample_id": biosample_id}).fetchall()
        downstream_document_ids: List[str] = [row[0] for row in rows]

        # Update all of those downstream documents so their `biosample_ids` array contains the `id`
        # of the current biosample.
        #
        # Note: We use Postgres's `array_append()` function to update the array. We use the `WHERE`
        #       clause to avoid adding the biosample's `id` to arrays that already contain it.
        #
        # Docs: https://www.postgresql.org/docs/current/functions-array.html
        #
        if len(downstream_document_ids) > 0:
            update_query = """--sql
                UPDATE biosample_related_document
                SET biosample_ids = array_append(biosample_ids, :biosample_id)
                WHERE id = ANY(:downstream_document_ids)
                  AND NOT (:biosample_id = ANY(biosample_ids));
            """
            db.execute(
                text(update_query),
                {
                    "biosample_id": biosample_id,
                    "downstream_document_ids": downstream_document_ids,
                },
            )


def delete_documents_having_no_associated_biosamples(db: Session) -> int:
    """
    Deletes all `BiosampleRelatedDocument` rows where the `biosample_ids` column consists
    of an empty array.
    """

    num_rows_deleted = (
        db.query(BiosampleRelatedDocument)
        .filter(func.cardinality(BiosampleRelatedDocument.biosample_ids) == 0)
        .delete(synchronize_session=False)
    )
    return num_rows_deleted


def load(db: Session, mongodb: Database) -> None:
    r"""
    Reads all documents from the MongoDB collections listed below; then, for each document,
    determines the IDs of (a) its immediate downstream neighbor(s), and (b) its associated
    biosample(s), and writes the document (without its `_id` field) and those determined things
    to the Postgres database.

    The MongoDB collections are:
    - `biosample_set`
    - `study_set`
    - `material_processing_set`
    - `processed_sample_set`
    - `data_generation_set`
    - `calibration_set`
    - `workflow_execution_set`
    - `data_object_set`
    """

    logger = get_logger(__name__)

    # Read the documents (omitting their `_id` fields) from the MongoDB database
    # and store them in the Postgres database.
    #
    # Note: We made some of the `load_...` functions return look-up tables that can be used by
    #       subsequently-invoked `load_...` functions. That way, we can avoid having to query
    #       the same collection multiple times. It is a performance optimization.
    #
    biosample_set = mongodb.get_collection("biosample_set")
    study_set = mongodb.get_collection("study_set")
    material_processing_set = mongodb.get_collection("material_processing_set")
    processed_sample_set = mongodb.get_collection("processed_sample_set")
    data_generation_set = mongodb.get_collection("data_generation_set")
    calibration_set = mongodb.get_collection("calibration_set")
    workflow_execution_set = mongodb.get_collection("workflow_execution_set")
    data_object_set = mongodb.get_collection("data_object_set")

    with duration_logger(logger, "🖥️ Loading workflow executions"):
        workflow_execution_has_input_values, workflow_execution_was_informed_by_values = (
            load_workflow_executions(db, workflow_execution_set)
        )
        workflow_execution_ids_by_input_id = invert_dict_of_lists(
            workflow_execution_has_input_values
        )
        workflow_execution_ids_by_informant_id = invert_dict_of_lists(
            workflow_execution_was_informed_by_values
        )
        db.commit()

    with duration_logger(logger, "🔬 Loading data generations"):
        data_generation_has_input_values = load_data_generations(
            db,
            data_generation_set,
            workflow_execution_ids_by_informant_id,
        )
        data_generation_ids_by_input_id = invert_dict_of_lists(data_generation_has_input_values)
        db.commit()

    with duration_logger(logger, "⚗️ Loading material processings"):
        material_processing_has_input_values = load_material_processings(
            db, material_processing_set
        )
        material_processing_ids_by_input_id = invert_dict_of_lists(
            material_processing_has_input_values
        )
        db.commit()

    with duration_logger(logger, "🧪 Loading biosamples"):
        biosample_ids, biosample_associated_studies_values = load_biosamples(
            db,
            biosample_set,
            data_generation_ids_by_input_id,
            material_processing_ids_by_input_id,
        )
        biosample_ids_by_associated_study_id = invert_dict_of_lists(
            biosample_associated_studies_values
        )
        db.commit()

    with duration_logger(logger, "📰 Loading studies"):
        load_studies(db, study_set, biosample_ids_by_associated_study_id)
        db.commit()

    with duration_logger(logger, "📐 Loading calibrations"):
        load_calibrations(db, calibration_set)
        db.commit()

    with duration_logger(logger, "🧪 Loading processed samples"):
        load_processed_samples(
            db,
            processed_sample_set,
            data_generation_ids_by_input_id,
            material_processing_ids_by_input_id,
        )
        db.commit()

    with duration_logger(logger, "💾 Loading data objects"):
        data_object_was_generated_by_values = load_data_objects(
            db, data_object_set, workflow_execution_ids_by_input_id
        )
        db.commit()

    with duration_logger(
        logger, "🪏 Backfilling downstream neighbor lists of data emitter processes"
    ):
        dict_of_strings = data_object_was_generated_by_values  # concise alias
        dict_of_lists = {
            data_object_id: [v] for data_object_id, v in dict_of_strings.items()
        }  # list-ify the (string) values
        generated_data_object_ids_by_data_emitter_process_id = invert_dict_of_lists(dict_of_lists)
        backfill_downstream_neighbor_lists_of_data_emitter_processes(
            db,
            generated_data_object_ids_by_data_emitter_process_id,
        )
        db.commit()

    # Use the downstream neighbor identities we gathered above to determine which biosample(s)
    # each document is associated with; and then update its `biosample_ids` column.
    with duration_logger(logger, "🕵️ Populating `biosample_ids` column"):
        populate_biosample_ids_column(db, biosample_ids)
        db.commit()

    # Clean up: Delete rows that have no associated biosample.
    with duration_logger(logger, "🧹 Deleting rows having no associated biosample"):
        num_rows_deleted = delete_documents_having_no_associated_biosamples(db)
        db.commit()
        logger.info(f"Deleted {num_rows_deleted} rows.")

    return None
