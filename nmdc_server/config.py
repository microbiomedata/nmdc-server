import os
from typing import Optional

from pydantic import BaseSettings
from starlette.config import Config


class Settings(BaseSettings):
    environment: str = "production"
    database_uri: str = "postgresql:///nmdc"
    testing_database_uri: str = "postgresql:///nmdc_testing"
    ingest_database_uri: str = "postgresql:///nmdc_testing"
    secret_key: str = "secret"
    client_id: str = "oauth client id"
    client_secret: str = "oauth secret key"
    open_id_config_url: str = "https://orcid.org/.well-known/openid-configuration"
    oauth_scope: str = "/authenticate"
    oauth_authorization_endpoint: str = "https://orcid.org/oauth/authorize"
    oauth_token_endpoint: str = "https://orcid.org/oauth/token"
    host: Optional[str] = None

    mongo_host: str = "nmdc-metadata.polyneme.xyz"
    mongo_database: str = "dwinston_share"
    mongo_user: str = ""
    mongo_password: str = ""

    celery_backend: str = "redis://redis:6379/0"
    celery_broker: str = "redis://redis:6379/0"

    sentry_dsn: Optional[str] = None

    class Config:
        env_prefix = "nmdc_"
        env_file = os.getenv("DOTENV_PATH", ".env")


settings = Settings()
starlette_config = Config(environ=settings.dict())  # for authlib, incompatible with pydantic config
