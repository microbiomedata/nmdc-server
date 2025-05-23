import os

import nmdc_geoloc_tools
import pytest
from factory import random
from starlette.testclient import TestClient

import nmdc_server.api
from nmdc_server import database, schemas
from nmdc_server.app import create_app
from nmdc_server.auth import create_token_response
from nmdc_server.config import settings
from nmdc_server.fakes import UserFactory
from nmdc_server.fakes import db as _db


@pytest.fixture(autouse=True)
def set_seed(connection):
    random.reseed_random("nmdc")


@pytest.fixture(autouse=True)
def patch_geo_engine(monkeypatch):
    """Patch all the nmdc_geoloc_tools functions that make external network requests."""

    def mock_get_elevation(lat_lon):
        lat, lon = lat_lon
        if not -90 <= lat <= 90:
            raise ValueError(f"Invalid Latitude: {lat}")
        if not -180 <= lon <= 180:
            raise ValueError(f"Invalid Longitude: {lon}")
        return 16.0

    def mock_not_implemented(*args, **kwargs):
        raise NotImplementedError()

    monkeypatch.setattr(nmdc_geoloc_tools, "elevation", mock_get_elevation)
    monkeypatch.setattr(nmdc_geoloc_tools, "fao_soil_type", mock_not_implemented)
    monkeypatch.setattr(nmdc_geoloc_tools, "landuse", mock_not_implemented)
    monkeypatch.setattr(nmdc_geoloc_tools, "landuse_dates", mock_not_implemented)


@pytest.fixture()
def patch_zip_stream_service(monkeypatch):
    def mock_zip_streamer(*args, **kwargs):
        yield b"foo"

    monkeypatch.setattr(nmdc_server.api, "stream_zip_archive", mock_zip_streamer)


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
