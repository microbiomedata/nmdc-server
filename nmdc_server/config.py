import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    database_uri: str = 'postgres://localhost:5432/nmdc'

    class Config:
        env_prefix = 'nmdc_'


settings = Settings(_env_file=os.getenv('DOTENV_PATH', '.env'))  # type: ignore
