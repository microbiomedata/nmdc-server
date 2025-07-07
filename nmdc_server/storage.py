from enum import StrEnum
from typing import Any

from google.auth.credentials import AnonymousCredentials
from google.cloud import storage

from nmdc_server.config import settings


class Bucket(StrEnum):
    """Enum for GCS bucket names"""

    SUBMISSION_IMAGES = "nmdc-submission-images"


def _initialize_client() -> storage.Client:
    client_args: dict[str, Any] = {
        "project": settings.gcs_project_id,
    }

    if settings.use_fake_gcs_server:
        # https://github.com/fsouza/fake-gcs-server/blob/cd43b03fcfb8149c6f57c1a92e19d1a07e291a3c/examples/python/python.py
        client_args["credentials"] = AnonymousCredentials()
        client_args["client_options"] = {"api_endpoint": "http://storage:4443"}

    return storage.Client(**client_args)


client = _initialize_client()
