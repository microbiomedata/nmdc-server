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

## API Access

Outside of the internal `nmdc-server` code, submission data can be accessed via several REST API endpoints:

- `GET /metadata_submission`: Returns a paginated list of submissions the current user has permission to see.
- `GET /metadata_submission/slim`: Returns a "slim" version of the list (with fewer fields) for faster loading in the UI.
- `GET /metadata_submission/{id}`: Returns the full details for a specific submission.

### Authorization
- Users can generally only access submissions they authored or have been granted a role on (owner, editor, viewer, etc.).
- **Admin-level authorization** is required to access or list all submissions across the entire system.