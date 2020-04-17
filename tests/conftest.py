import os

import pytest
from starlette.testclient import TestClient

from nmdc_server import database
from nmdc_server.app import create_app
from nmdc_server.config import Settings


@pytest.fixture
def db():
    settings = Settings()
    settings.database_uri = settings.testing_database_uri
    with database.create_session(settings) as db:
        database.Base.metadata.create_all()
        yield db
        database.Base.metadata.drop_all()


@pytest.fixture
def app(db):
    return create_app(env=os.environ.copy())


@pytest.fixture
def client(app):
    return TestClient(app)
