import re
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from functools import cached_property
from pathlib import PurePath
from typing import Any, Iterable

from google.auth.credentials import AnonymousCredentials
from google.cloud.exceptions import NotFound
from google.cloud.storage import Blob, Bucket, Client

from nmdc_server.config import settings
from nmdc_server.schemas import SignedUrl


class BucketName(StrEnum):
    """Enum for GCS bucket names"""

    SUBMISSION_IMAGES = settings.gcs_submission_images_bucket_name


class Storage:
    """A class to manage Google Cloud Storage interactions."""

    def __init__(self):
        self._is_testing = settings.environment == "testing"

    @cached_property
    def _client(self):
        """Google Cloud Storage client."""
        client_args: dict[str, Any] = {
            "project": settings.gcs_project_id,
        }

        if self._is_testing:
            client_args["credentials"] = AnonymousCredentials()

        if settings.gcs_use_fake:
            client_args["client_options"] = {"api_endpoint": settings.gcs_fake_api_endpoint}

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
        expiration_delta = timedelta(minutes=expiration)
        expiration_time = datetime.now(timezone.utc) + expiration_delta

        if self._is_testing:
            # In testing mode, we use AnonymousCredentials which do not support signed URLs. There
            # is also no need to generate real signed URLs during tests, so we return a mock URL.
            return SignedUrl(
                url=f"{settings.gcs_fake_access_endpoint}/{bucket_name}/{object_name}",
                expiration=expiration_time,
                object_name=object_name,
            )

        blob = self.get_object(bucket_name, object_name)

        url = blob.generate_signed_url(
            version="v4",
            expiration=expiration_delta,
            method=method,
            content_type=content_type,
            api_access_endpoint=(
                settings.gcs_fake_access_endpoint if settings.gcs_use_fake else None
            ),
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


storage = Storage()


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename according to GCS requirements and recommendations.

    See: https://cloud.google.com/storage/docs/objects#naming

    :param filename: The original filename to sanitize.
    :return: The sanitized filename.
    """
    path = PurePath(filename)

    basename = path.stem
    suffix = path.suffix

    # Remove leading periods
    basename = re.sub(r"^\.+", "", basename)

    # Remove reserved characters
    basename = re.sub(r'[#\[\]*?:"<>|]', "", basename)

    # Remove control characters
    basename = re.sub(r"[\x7F-\x84\x86-\x9F]", "", basename)

    # Remove newline characters
    basename = re.sub(r"[\x0A\x0D]", "", basename)

    combined = basename + suffix

    # Limit to 512 UTF-8 bytes
    utf8_bytes = combined.encode("utf-8")
    max_total_bytes = 512
    total_bytes = len(utf8_bytes)
    if total_bytes > max_total_bytes:
        # Truncate (from the start) to fit within 512 bytes, ensuring we don't cut a multibyte
        # character
        start_byte = total_bytes - max_total_bytes
        # (b & 0xC0) == 0x80 checks if the byte b is a continuation byte in UTF-8
        # https://en.wikipedia.org/wiki/UTF-8#Description
        while start_byte <= total_bytes and (utf8_bytes[start_byte] & 0xC0) == 0x80:
            start_byte += 1
        combined = utf8_bytes[start_byte:].decode("utf-8", errors="ignore")

    return combined
