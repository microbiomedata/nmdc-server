from google.auth.credentials import AnonymousCredentials
from google.cloud import storage

from nmdc_server.config import settings

client_args = {
    "project": settings.gcs_project_id,
}

if settings.use_fake_gcs_server:
    # https://github.com/fsouza/fake-gcs-server/blob/cd43b03fcfb8149c6f57c1a92e19d1a07e291a3c/examples/python/python.py
    client_args["credentials"] = AnonymousCredentials()
    client_args["client_options"] = {"api_endpoint": "http://storage:4443"}

client = storage.Client(**client_args)
