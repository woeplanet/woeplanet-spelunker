"""
WOEplanet Spelunker: tests package; pytest fixtures.
"""

from collections.abc import Iterator

import pytest
from starlette.testclient import TestClient

from woeplanet.spelunker.server import app


@pytest.fixture(scope='session')
def client() -> Iterator[TestClient]:
    """
    Test client with lifespan management.
    """

    with TestClient(app) as client:
        yield client
