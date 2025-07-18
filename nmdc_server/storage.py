from datetime import datetime, timedelta, timezone
from enum import StrEnum
from functools import cached_property
from typing import Any

from google.cloud import storage as gcs, exceptions as gce

from nmdc_server.config import settings
from nmdc_server.schemas import SignedUrl


class BucketName(StrEnum):
    """Enum for GCS bucket names"""

    SUBMISSION_IMAGES = "nmdc-submission-images"


class Storage:
    """A class to manage Google Cloud Storage interactions."""

    def __init__(self, project_id: str, use_fake_gcs_server: bool):
        self.project_id = project_id
        self.use_fake_gcs_server = use_fake_gcs_server

    @cached_property
    def _client(self):
        """Google Cloud Storage client."""
        client_args: dict[str, Any] = {
            "project": self.project_id,
        }

        if self.use_fake_gcs_server:
            client_args["client_options"] = {"api_endpoint": "http://storage:4443"}

        return gcs.Client(**client_args)

    def get_bucket(self, bucket_name: BucketName) -> gcs.Bucket:
        """Get a GCS bucket by name.

        :param bucket_name: The name of the bucket to retrieve.
        """
        return self._client.bucket(bucket_name)

    def get_object(self, bucket_name: BucketName, object_name: str) -> gcs.Blob:
        """Get an object from a GCS bucket.

        :param bucket_name: The name of the bucket containing the object.
        :param object_name: The name of the object to retrieve.
        """
        bucket = self.get_bucket(bucket_name)
        return bucket.blob(object_name)

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
        except gce.NotFound as e:
            if raise_if_not_found:
                raise e

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
        blob = self.get_object(bucket_name, object_name)
        expiration_delta = timedelta(minutes=expiration)
        expiration_time = datetime.now(timezone.utc) + expiration_delta

        url = blob.generate_signed_url(
            version="v4",
            expiration=expiration_delta,
            method="PUT",
            content_type=content_type,
        )

        if self.use_fake_gcs_server:
            # If using a fake GCS server, we need to adjust the URL to point localhost instead of
            # the docker-compose service name.
            url = url.replace("//storage:", "//localhost:")

        return SignedUrl(url=url, expiration=expiration_time, object_name=blob.name)

    def get_signed_download_url(
        self, bucket_name: BucketName, object_name: str, *, expiration: int = 15
    ) -> SignedUrl:
        """Get a signed URL for downloading an object from a GCS bucket.

        :param bucket_name: The name of the bucket containing the object.
        :param object_name: The name of the object to download.
        :param expiration: The expiration time for the signed URL in minutes. Default is 15 minutes.
        """
        expiration_delta = timedelta(minutes=expiration)
        expiration_time = datetime.now(timezone.utc) + expiration_delta
        blob = self.get_object(bucket_name, object_name)
        url = blob.generate_signed_url(
            version="v4",
            expiration=expiration_delta,
            method="GET",
        )

        if self.use_fake_gcs_server:
            # If using a fake GCS server, we need to adjust the URL to point localhost instead of
            # the docker-compose service name.
            url = url.replace("//storage:", "//localhost:")

        return SignedUrl(
            url=url,
            object_name=blob.name,
            expiration=expiration_time,
        )


storage = Storage(
    project_id=settings.gcs_project_id,
    use_fake_gcs_server=settings.use_fake_gcs_server,
)
