import os

import pytest
from factory import random
from starlette.requests import Request
from starlette.testclient import TestClient

from nmdc_server import auth, crud, database, schemas
from nmdc_server.app import create_app
from nmdc_server.config import settings
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
def set_seed(connection):
    random.reseed_random("nmdc")


@pytest.fixture(scope="session")
def connection():
    assert settings.environment == "testing"
    try:
        database.metadata.drop_all()
        database.metadata.create_all()
        yield _db
    finally:
        _db.rollback()
        database.metadata.drop_all()
        _db.remove()


@pytest.fixture
def db(connection):
    yield connection
    connection.rollback()
    for table in reversed(database.metadata.sorted_tables):
        connection.execute(table.delete())
    connection.commit()


@pytest.fixture
def app(db):
    return create_app(env=os.environ.copy(), secure_cookies=False)


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def token(client):
    resp = client.post("/test-session")
    return auth.Token(**resp.json())


@pytest.fixture
def logged_in_user(token):
    user_schema = schemas.User(name=token.name, orcid=token.orcid)
    user = crud.get_or_create_user(_db, user_schema)
    return user
