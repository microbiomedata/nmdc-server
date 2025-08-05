from __future__ import annotations

import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "production"
    debug: bool = False

    # Several different database urls are configured for different
    # environments.  In production, only database_uri and ingest_database_uri
    # are used.
    database_uri: str = "postgresql:///nmdc"
    ingest_database_uri: str = "postgresql:///nmdc_testing"
    testing_database_uri: str = "postgresql:///nmdc_testing"

    nmdc_ontology_version: str = "2024-03-15"

    # database tuning knobs
    # Note the important relationship between postgres max connections, the pool size
    # per worker (this number), and the number of uvicorn workers, each of which has
    # its own engine / pool. Tune the deployment accordingly.
    db_pool_size: int = 5
    # Pool overflow means that if all keep-alive pool connections are in use,
    # up to this many extra connections will be opened but then immediately closed
    # after the session closes.
    db_pool_max_overflow: int = 3

    # These values control the JWTs issued by nmdc-server as access and refresh tokens
    api_jwt_secret: str = "generate me"
    api_jwt_expiration: int = 24 * 60 * 60  # 24 hours
    api_jwt_refresh_expiration: int = 60 * 60 * 24 * 365  # 365 days

    # for orcid oauth
    session_secret_key: str = "secret"
    orcid_base_url: str = "https://orcid.org"
    orcid_client_id: str = "oauth client id"
    orcid_client_secret: str = "oauth secret key"
    orcid_authorize_scope: str = "/authenticate"

    # for zipstreamer
    zip_streamer_url: str = "http://zipstreamer:4008/download"
    zip_streamer_chunk_size_bytes: int = 2 * 1024 * 1024
    zip_streamer_nersc_data_base_url: str = "https://data.microbiomedata.org/data"

    # for cloud storage
    gcs_use_fake: bool = True
    """If true, use the fake GCS server for local development."""

    gcs_fake_api_endpoint: str = "http://storage:4443"
    """The fake GCS server API endpoint. 
    
    This is only used if gcs_use_fake is True. This is used by the backend to communicate with the
    fake GCS server, so it should typically refer to the docker compose service name."""

    gcs_fake_access_endpoint: str = "http://localhost:4443"
    """The fake GCS server access endpoint. 
    
    This is only used if gcs_use_fake is True. This is used when producing signed URLs that the
    frontend will use, so it should typically refer to the localhost address."""

    gcs_project_id: str | None = None
    """The GCS project ID. This is only required if gcs_use_fake is False."""

    gcs_object_name_prefix: str
    """Prefix for GCS object names. 
    
    This is used to organize objects in the bucket. This must be set in the .env file or as an
    environment variable."""

    gcs_submission_images_bucket_name: str = "nmdc-submission-images"
    """The name of the GCS bucket used for submission images."""

    max_submission_image_file_size_bytes: int = 25 * 1000 * 1000  # 25 MB
    """The maximum size of a single submission image file in bytes."""

    max_submission_image_total_size_bytes: int = 1 * 1000 * 1000 * 1000  # 1 GB
    """The maximum total size of all submission image files for a single submission in bytes."""

    @property
    def orcid_openid_config_url(self) -> str:
        r"""
        Derives the `orcid_openid_config_url` field's value based upon another field's value.
        Note: This project currently depends upon Pydantic version 1, which does not offer
              the `@computed_field` decorator offered by Pydantic version 2. So, we implement
              a "getter" method using Python's built-in `@property` decorator instead.
              References:
              - https://docs.python.org/3/library/functions.html#property
              - https://docs.pydantic.dev/2.7/concepts/fields/#the-computed_field-decorator
        """
        return f"{self.orcid_base_url}/.well-known/openid-configuration"

    # host name for the ORCID oauth2 redirect and our own JWT issuer
    host: str = "http://127.0.0.1:8000"

    # mongo database used for ingest
    mongo_host: str = "mongo-loadbalancer.nmdc-runtime-dev.development.svc.spin.nersc.org"
    mongo_port: int = 27017
    mongo_database: str = "nmdc"
    mongo_user: str = ""
    mongo_password: str = ""

    # celery broker for ingest/migration jobs
    celery_backend: str = "redis://redis:6379/0"
    celery_broker: str = "redis://redis:6379/0"

    sentry_dsn: Optional[str] = None

    # Enable/disable and configure tracing through environment
    # variables to lessen friction when fine-tuning settings
    # for useful tracing.
    sentry_tracing_enabled: bool = False
    sentry_traces_sample_rate: float = 0.0

    print_sql: bool = False

    # App settings related to UI behavior
    disable_bulk_download: str = ""
    portal_banner_title: Optional[str] = None
    portal_banner_message: Optional[str] = None

    # Rancher information to swap databases after ingest
    rancher_api_base_url: Optional[str] = None
    rancher_api_auth_token: Optional[str] = None
    rancher_project_id: Optional[str] = None
    rancher_postgres_secret_id: Optional[str] = None
    rancher_backend_workload_id: Optional[str] = None
    rancher_worker_workload_id: Optional[str] = None

    # Parameters related to posting messages to Slack.
    # Reference: https://api.slack.com/messaging/webhooks
    slack_webhook_url_for_ingester: Optional[str] = None

    # CORS settings necessary for allowing request from Field Notes app
    cors_allow_origins: Optional[str] = None  # comma separated list of allowed origins

    # Comma separated list of allowed origins for post-login redirect
    login_redirect_allow_origins: str = "http://127.0.0.1:8081,http://127.0.0.1:8080"
    # Github Issue creation settings. Both are required for automated issue creation.
    github_issue_url: Optional[str] = None
    github_authentication_token: Optional[str] = None
    github_issue_assignee: Optional[str] = None

    @property
    def current_db_uri(self) -> str:
        if self.environment == "testing":
            return self.testing_database_uri
        return self.database_uri

    model_config = SettingsConfigDict(
        env_prefix="nmdc_",
        env_file=os.getenv("DOTENV_PATH", ".env"),
        extra="allow",
    )


settings = Settings()
