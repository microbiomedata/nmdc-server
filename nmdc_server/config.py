import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    database_uri: str = "postgresql://localhost:5432/nmdc"
    testing_database_uri: str = "postgresql://localhost:5432/nmdc_testing"

    class Config:
        env_prefix = "nmdc_"
        env_file = os.getenv("DOTENV_PATH", ".env")


settings = Settings()
