import os
from typing import Callable, Generator

import nmdc_geoloc_tools
import pytest
from factory import random
from google.cloud.storage import Blob
from starlette.testclient import TestClient

import nmdc_server.api
from nmdc_server import database, schemas
from nmdc_server.app import create_app
from nmdc_server.auth import create_token_response
from nmdc_server.config import settings
from nmdc_server.database import engine
from nmdc_server.fakes import UserFactory
from nmdc_server.fakes import db as _db
from nmdc_server.storage import BucketName, storage


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
        database.metadata.drop_all(bind=engine)
        database.metadata.create_all(bind=engine)
        yield _db
    finally:
        _db.rollback()
        database.metadata.drop_all(bind=engine)
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


@pytest.fixture
def temp_storage_object() -> Generator[Callable[[BucketName, str], Blob], None, None]:
    """Get a function to create temporary storage objects for testing."""
    blobs: list[tuple[BucketName, str]] = []

    def _temp_storage_object(bucket_name: BucketName, object_name: str) -> Blob:
        bucket = storage.get_bucket(bucket_name)
        tmp_blob = bucket.blob(object_name)
        tmp_blob.upload_from_string("Temporary content for testing")
        blobs.append((bucket_name, object_name))
        return tmp_blob

    yield _temp_storage_object

    # Cleanup temporary storage objects
    for bucket_name, object_name in blobs:
        # Use raise_if_not_found=False because the test may have already deleted the object
        storage.delete_object(bucket_name, object_name, raise_if_not_found=False)
