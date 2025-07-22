from datetime import datetime, timedelta, timezone
from enum import StrEnum
from functools import cached_property
from typing import Any, Iterable

from google.auth.credentials import AnonymousCredentials
from google.cloud.exceptions import NotFound
from google.cloud.storage import Blob, Bucket, Client

from nmdc_server.config import settings
from nmdc_server.schemas import SignedUrl


class BucketName(StrEnum):
    """Enum for GCS bucket names"""

    SUBMISSION_IMAGES = "nmdc-submission-images"


class Storage:
    """A class to manage Google Cloud Storage interactions."""

    def __init__(self, project_id: str | None, use_fake_server: bool):
        self.project_id = project_id
        self.use_fake_server = use_fake_server

        self._is_testing = settings.environment == "testing"

    @cached_property
    def _client(self):
        """Google Cloud Storage client."""
        client_args: dict[str, Any] = {
            "project": self.project_id,
        }

        if self._is_testing:
            client_args["credentials"] = AnonymousCredentials()
            client_args["client_options"] = {"api_endpoint": "http://localhost:4443"}
        elif self.use_fake_server:
            client_args["client_options"] = {"api_endpoint": "http://storage:4443"}

        return Client(**client_args)

    def get_bucket(self, bucket_name: BucketName) -> Bucket:
        """Get a GCS bucket by name.

        :param bucket_name: The name of the bucket to retrieve.
        """
        return self._client.bucket(bucket_name)

    def get_object(self, bucket_name: BucketName, object_name: str) -> Blob:
        """Get an object from a GCS bucket.

        :param bucket_name: The name of the bucket containing the object.
        :param object_name: The name of the object to retrieve.
        """
        bucket = self.get_bucket(bucket_name)
        return bucket.blob(object_name)

    def iter_objects(self, bucket_name: BucketName, prefix: str | None = None) -> Iterable[Blob]:
        """Iterate over objects in a GCS bucket.

        :param bucket_name: The name of the bucket to iterate over.
        :param prefix: Optional prefix to filter objects by.
        """
        bucket = self.get_bucket(bucket_name)
        return bucket.list_blobs(prefix=prefix)

    def delete_object(
        self, bucket_name: BucketName, object_name: str, *, raise_if_not_found: bool = False
    ) -> None:
        """Delete an object from a GCS bucket.

        :param bucket_name: The name of the bucket containing the object.
        :param object_name: The name of the object to delete.
        :param raise_if_not_found: If True, raise an exception if the object is not found. Default
            is False.
        """
        bucket = self.get_bucket(bucket_name)
        try:
            bucket.delete_blob(object_name)
        except NotFound as e:
            if raise_if_not_found:
                raise e

    def _get_signed_url(
        self,
        bucket_name: BucketName,
        object_name: str,
        method: str,
        *,
        expiration: int = 15,
        content_type: str | None = None,
    ) -> SignedUrl:
        """Get a signed URL for an object in a GCS bucket.

        :param bucket_name: The name of the bucket containing the object.
        :param object_name: The name of the object.
        :param method: The HTTP method for the signed URL (e.g., 'GET', 'PUT').
        :param expiration: The expiration time for the signed URL in minutes. Default is 15 minutes.
        :param content_type: The content type of the object being uploaded (for PUT requests).
        """
        if self._is_testing:
            # In testing mode, we use AnonymousCredentials which do not support signed URLs.
            return SignedUrl(
                url=f"http://localhost:4443/{bucket_name}/{object_name}",
                expiration=datetime.now(timezone.utc),
                object_name=object_name,
            )

        blob = self.get_object(bucket_name, object_name)
        expiration_delta = timedelta(minutes=expiration)
        expiration_time = datetime.now(timezone.utc) + expiration_delta

        url = blob.generate_signed_url(
            version="v4",
            expiration=expiration_delta,
            method=method,
            content_type=content_type,
            api_access_endpoint="http://localhost:4443" if self.use_fake_server else None,
        )

        return SignedUrl(url=url, expiration=expiration_time, object_name=blob.name)

    def get_signed_upload_url(
        self,
        bucket_name: BucketName,
        object_name: str,
        *,
        expiration: int = 15,
        content_type: str | None = None,
    ) -> SignedUrl:
        """Get a signed URL for uploading to an object to a GCS bucket.

        :param bucket_name: The name of the bucket that will contain the object.
        :param object_name: The name of the object.
        :param expiration: The expiration time for the signed URL in minutes. Default is 15 minutes.
        :param content_type: The content type of the object being uploaded.
        """
        return self._get_signed_url(
            bucket_name=bucket_name,
            object_name=object_name,
            method="PUT",
            expiration=expiration,
            content_type=content_type,
        )

    def get_signed_download_url(
        self, bucket_name: BucketName, object_name: str, *, expiration: int = 15
    ) -> SignedUrl:
        """Get a signed URL for downloading an object from a GCS bucket.

        :param bucket_name: The name of the bucket containing the object.
        :param object_name: The name of the object to download.
        :param expiration: The expiration time for the signed URL in minutes. Default is 15 minutes.
        """
        return self._get_signed_url(
            bucket_name=bucket_name,
            object_name=object_name,
            method="GET",
            expiration=expiration,
        )


storage = Storage(
    project_id=settings.gcs_project_id,
    use_fake_server=settings.gcs_use_fake,
)
