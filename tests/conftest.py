import os

from factory import random
import pytest
from starlette.testclient import TestClient

from nmdc_server import database
from nmdc_server.app import create_app
from nmdc_server.database import create_engine
from nmdc_server.fakes import db as _db


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
