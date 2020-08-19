import os

from pydantic import BaseSettings
from starlette.config import Config


class Settings(BaseSettings):
    database_uri: str = "postgresql:///nmdc"
    testing_database_uri: str = "postgresql:///nmdc_testing"
    secret_key: str = "secret"
    client_id: str = "oauth client id"
    client_secret: str = "oauth secret key"
    open_id_config_url: str = "https://orcid.org/.well-known/openid-configuration"
    oauth_scope: str = "/authenticate"
    oauth_authorization_endpoint: str = "https://orcid.org/oauth/authorize"
    oauth_token_endpoint: str = "https://orcid.org/oauth/token"

    class Config:
        env_prefix = "nmdc_"
        env_file = os.getenv("DOTENV_PATH", ".env")


settings = Settings()
starlette_config = Config(environ=settings.dict())  # for authlib, incompatible with pydantic config
