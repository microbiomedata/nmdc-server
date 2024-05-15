import os
from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    environment: str = "production"

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
    orcid_client_id: str = "oauth client id"
    orcid_client_secret: str = "oauth secret key"
    orcid_openid_config_url: str = "https://orcid.org/.well-known/openid-configuration"
    orcid_authorize_scope: str = "/authenticate"
    host: Optional[str] = None  # sets the host name for the oauth2 redirect

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

    print_sql: bool = False

    # App settings related to UI behavior
    disable_bulk_download: str = ""

    # Rancher information to swap databases after ingest
    rancher_api_base_url: Optional[str] = None
    rancher_api_auth_token: Optional[str] = None
    rancher_project_id: Optional[str] = None
    rancher_postgres_secret_id: Optional[str] = None
    rancher_backend_workload_id: Optional[str] = None
    rancher_worker_workload_id: Optional[str] = None

    # CORS settings necessary for allowing request from Field Notes app
    cors_allow_origins: Optional[str] = None  # comma separated list of allowed origins

    # Comma separated list of allowed origins for post-login redirect
    login_redirect_allow_origins: str = "http://127.0.0.1:8081"

    # Github Issue creation settings. Both are required for automated issue creation.
    github_issue_url: Optional[str] = None
    github_authentication_token: Optional[str] = None
    github_issue_assignee: Optional[str] = None

    @property
    def current_db_uri(self) -> str:
        if self.environment == "testing":
            return self.testing_database_uri
        return self.database_uri

    class Config:
        env_prefix = "nmdc_"
        env_file = os.getenv("DOTENV_PATH", ".env")


settings = Settings()
