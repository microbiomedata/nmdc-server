import os

import pytest
from starlette.testclient import TestClient

from nmdc_server.app import create_app


@pytest.fixture
def app():
    return create_app(env=os.environ.copy())


@pytest.fixture
def client(app):
    return TestClient(app)
