import os

import pytest
from factory import random
from starlette.testclient import TestClient

from nmdc_server import database, schemas
from nmdc_server.app import create_app
from nmdc_server.auth import create_token_response
from nmdc_server.config import settings
from nmdc_server.fakes import UserFactory
from nmdc_server.fakes import db as _db


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
    return create_app(env=os.environ.copy())


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def logged_in_user(db, client) -> schemas.User:
    user = UserFactory()
    db.commit()

    token_response = create_token_response(user)
    client.headers["Authorization"] = f"Bearer {token_response.access_token.decode()}"

    return user


@pytest.fixture
def logged_in_admin_user(db, client) -> schemas.User:
    r"""
    Returns a logged-in user that is an admin.

    TODO: Consider adding an `is_admin: bool = False` parameter to the `logged_in_user` fixture
          and then consolidating this fixture with that one.
    """

    user = UserFactory(is_admin=True)
    db.commit()

    token_response = create_token_response(user)
    client.headers["Authorization"] = f"Bearer {token_response.access_token.decode()}"

    return user
