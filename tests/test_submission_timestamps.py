from datetime import datetime
from uuid import uuid4

from nmdc_schema.nmdc import SubmissionStatusEnum
from sqlalchemy.orm import Session

from nmdc_server import models
from nmdc_server.ingest.common import merge_download_artifact


def make_sample_set(
    submission_id: str, *, date_last_modified: datetime | None = None
) -> models.SubmissionSampleSet:
    return models.SubmissionSampleSet(
        id=uuid4(),
        submission_metadata_id=submission_id,
        name="Sample Set",
        created=datetime(2020, 1, 1),
        date_last_modified=date_last_modified,
        status=SubmissionStatusEnum.InProgress.text,
        templates=[],
        sample_environment_form={},
        sender_shipping_info_form={},
        multi_omics_form={},
        sample_data={},
    )


def test_merge_preserves_submission_timestamps(db: Session):
    """
    Test that the ingest's merge_download_artifact function preserves the date_last_modified
    timestamps of submissions and sample sets.
    """
    original_timestamp = datetime(2020, 1, 2)
    submission = models.SubmissionMetadata(
        id=uuid4(),
        author_orcid="test",
        created=datetime(2020, 1, 1),
        date_last_modified=original_timestamp,
    )
    sample_set = make_sample_set(
        submission.id,
        date_last_modified=original_timestamp,
    )

    merge_download_artifact(db, [submission])
    merge_download_artifact(db, [sample_set])

    copied_submission = db.get(models.SubmissionMetadata, submission.id)  # type: ignore[attr-defined]
    copied_sample_set = db.get(models.SubmissionSampleSet, sample_set.id)  # type: ignore[attr-defined]

    assert copied_submission is not None
    assert copied_sample_set is not None
    assert copied_submission.date_last_modified == original_timestamp
    assert copied_sample_set.date_last_modified == original_timestamp


def test_new_sample_set_without_timestamp_updates_parent(db: Session):
    """
    Test that creating a new sample set without a date_last_modified timestamp (simulating how a new
    sample set created through the Submission Portal would look) updates the parent submission's
    date_last_modified timestamp.
    """
    submission = models.SubmissionMetadata(author_orcid="test")
    db.add(submission)
    db.commit()
    original_submission_timestamp = submission.date_last_modified

    sample_set = make_sample_set(submission.id)
    db.add(sample_set)
    db.commit()
    db.refresh(submission)

    assert sample_set.date_last_modified is not None
    assert submission.date_last_modified == sample_set.date_last_modified
    assert submission.date_last_modified >= original_submission_timestamp


def test_mutating_sample_set_updates_parent_timestamp(db: Session):
    """
    Test that mutating a sample set updates the parent submission's date_last_modified timestamp.
    """
    original_timestamp = datetime(2020, 1, 2)
    submission = models.SubmissionMetadata(
        author_orcid="test",
        date_last_modified=original_timestamp,
    )
    db.add(submission)
    db.commit()
    sample_set = make_sample_set(
        submission.id,
        date_last_modified=original_timestamp,
    )
    db.add(sample_set)
    db.commit()

    sample_set.name = "Updated Sample Set"
    db.commit()
    db.refresh(submission)

    assert sample_set.date_last_modified > original_timestamp
    assert submission.date_last_modified == sample_set.date_last_modified
