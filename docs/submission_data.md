# Submission Data Storage and Access

This document describes how metadata submission data is stored in the `nmdc-server` database and how it is accessed.

## Database Representation

Each metadata submission is represented by a single row in the `submission_metadata` table in the PostgreSQL database.

### SQLAlchemy Model
The primary interaction point for submission data within the `nmdc-server` Python code is the `SubmissionMetadata` SQLAlchemy model, defined in `nmdc_server/models.py`.

The fields in the `SubmissionMetadata` model serve several purposes:
- **Linkages**: Connections to other tables, such as the `author_id` (linking to the `User` table).
- **Search and Sort**: Copies of specific information from the submission forms (e.g., `study_name`, `status`, `created`) are stored in dedicated columns to make database-level searching, filtering, and sorting more efficient.
- **Form Data**: The complete, detailed form data is stored in a `JSONB` column named `metadata_submission`.

## Data Structure

### Form Data (JSONB)
The structure of the objects stored in the `metadata_submission` column is governed by Pydantic models in `nmdc_server/schemas_submission.py`. The root model for a full submission record is `MetadataSubmissionRecord`.

This record includes several sub-forms:
- `studyForm`: General information about the study.
- `multiOmicsForm`: Details about the omics processing types and protocols.
- `addressForm`: Shipping and contact information.
- `sampleData`: The actual sample metadata.

### Sample Metadata
The `sampleData` field within the `metadata_submission` JSONB object contains the rows of metadata edited via DataHarmonizer.
- The structure of this field follows the [NMDC Submission Schema `SampleData` class](https://microbiomedata.github.io/submission-schema/SampleData/).
- It is stored as a dictionary where keys are template names and values are lists of sample rows.

## Code Examples

### Accessing Submission Data
In the backend code, you will frequently see `SubmissionMetadata` accessed via the SQLAlchemy session.

**Example: Fetching by ID (from `nmdc_server/api.py`)**
```python
submission = db.get(models.SubmissionMetadata, id)
```

**Example: Querying and Filtering (from `nmdc_server/crud.py`)**
```python
all_submissions = (
    db.query(models.SubmissionMetadata)
    .filter(models.SubmissionMetadata.status == SubmissionStatusEnum.SubmittedPendingReview.text)
)
```

## Data Flow and Submission Process

### User Edits
As users interact with the Submission Portal forms and DataHarmonizer, the `submission_metadata` table in the PostgreSQL database is updated in real-time. This means that while a submission's status is `InProgress`, it may contain incomplete or temporarily incorrect information. This is expected behavior as the data is actively being drafted.

### Review and Ingestion
When a user officially submits their submission, it enters a manual review phase. During this time, NMDC staff review the submission for completeness and accuracy.

Once the manual review is successfully completed, the submission data is finalized and prepared for ingestion into MongoDB.

### Translation to NMDC Schema
The final stage of the data flow involves translating the submission record into formal NMDC schema objects (e.g., `Study`, `Biosample`, `NucleotideSequencing`). This process is managed by a Dagster job within the `nmdc-runtime` environment. The `nmdc-runtime` code fetches the submission metadata from `nmdc-server` and uses a [dedicated translator](https://github.com/microbiomedata/nmdc-runtime/blob/273bb0d738deafdf7ff55e7a3904f3d9be00801d/nmdc_runtime/site/translation/submission_portal_translator.py) to map the JSONB form data into standard `nmdc-schema` instances.

## API Access

Outside of the internal `nmdc-server` code, submission data can be accessed via several REST API endpoints:

- `GET /metadata_submission`: Returns a paginated list of submissions the current user has permission to see.
- `GET /metadata_submission/slim`: Returns a "slim" version of the list (with fewer fields) for faster loading in the UI.
- `GET /metadata_submission/{id}`: Returns the full details for a specific submission.

### Authorization
- Users can generally only access submissions they authored or have been granted a role on (owner, editor, viewer, etc.).
- **Admin-level authorization** is required to access or list all submissions across the entire system.