import os

import pytest
from starlette.testclient import TestClient

from nmdc_server import database
from nmdc_server.app import create_app
from nmdc_server.config import Settings
from nmdc_server.database import create_engine
from nmdc_server.fakes import db as _db


@pytest.fixture(scope="module")
def connection():
    settings = Settings()
    settings.testing_database_uri = settings.testing_database_uri
    engine = create_engine(testing=True)
    database.Base.metadata.bind = engine
    _db.configure(bind=engine)
    try:
        database.Base.metadata.create_all()
        yield _db
    finally:
        _db.rollback()
        database.Base.metadata.drop_all()
        _db.remove()


@pytest.fixture
def db(connection):
    yield connection
    connection.rollback()
    for table in reversed(database.Base.metadata.sorted_tables):
        connection.execute(table.delete())
    connection.commit()


@pytest.fixture
def app(db):
    return create_app(env=os.environ.copy())


@pytest.fixture
def client(app):
    return TestClient(app)
