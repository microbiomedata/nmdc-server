import os

import pytest
from factory import random
from starlette.requests import Request
from starlette.testclient import TestClient

from nmdc_server import auth, database
from nmdc_server.app import create_app
from nmdc_server.config import settings
from nmdc_server.database import create_engine
from nmdc_server.fakes import TokenFactory
from nmdc_server.fakes import db as _db


@auth.router.post("/test-session", include_in_schema=False)
async def create_test_session(request: Request) -> auth.Token:
    token = TokenFactory()
    data = token.dict()
    data["access_token"] = str(data["access_token"])
    data["refresh_token"] = str(data["refresh_token"])
    request.session["token"] = data
    return token


@pytest.fixture(autouse=True)
def testing_environment():
    settings.environment = "testing"
    return settings


@pytest.fixture(autouse=True)
def set_seed(connection):
    random.reseed_random("nmdc")


@pytest.fixture(scope="module")
def connection():
    database.testing = True
    engine = create_engine()
    database.metadata.bind = engine
    _db.configure(bind=engine)
    try:
        database.metadata.drop_all()
        database.metadata.create_all()
        yield _db
    finally:
        _db.rollback()
        database.metadata.drop_all()
        _db.remove()
        database.testing = False


@pytest.fixture
def db(connection):
    yield connection
    connection.rollback()
    for table in reversed(database.metadata.sorted_tables):
        connection.execute(table.delete())
    connection.commit()


@pytest.fixture
def app(db):
    return create_app(env=os.environ.copy())


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def token(client):
    resp = client.post("/test-session")
    return auth.Token(**resp.json())
