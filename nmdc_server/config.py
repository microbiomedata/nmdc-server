import os
from typing import Optional

from pydantic import BaseSettings
from starlette.config import Config


class Settings(BaseSettings):
    environment: str = "production"

    # Several different database urls are configured for different
    # environments.  In production, only database_uri and ingest_database_uri
    # are used.
    database_uri: str = "postgresql:///nmdc_testing"
    ingest_database_uri: str = "postgresql:///nmdc_testing"
    testing_database_uri: str = "postgresql:///nmdc_testing"

    # database tuning knobs
    # Note the important relationship between postgres max connections, the pool size
    # per worker (this number), and the number of uvicorn workers, each of which has
    # its own engine / pool. Tune the deployment accordingly.
    db_pool_size: int = 5
    # Pool overflow means that if all keep-alive pool connections are in use,
    # up to this many extra connections will be opened but then immediately closed
    # after the session closes.
    db_pool_max_overflow: int = 3

    # for orcid oauth
    secret_key: str = "secret"
    client_id: str = "oauth client id"
    client_secret: str = "oauth secret key"
    open_id_config_url: str = "https://orcid.org/.well-known/openid-configuration"
    oauth_scope: str = "/authenticate"
    oauth_authorization_endpoint: str = "https://orcid.org/oauth/authorize"
    oauth_token_endpoint: str = "https://orcid.org/oauth/token"
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

    @property
    def current_db_uri(self) -> str:
        if self.environment == "testing":
            return self.testing_database_uri
        return self.database_uri

    class Config:
        env_prefix = "nmdc_"
        env_file = os.getenv("DOTENV_PATH", ".env")


settings = Settings()
starlette_config = Config(environ=settings.dict())  # for authlib, incompatible with pydantic config
