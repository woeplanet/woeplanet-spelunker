"""
WOEplanet Spelunker: tests package; pytest fixtures.
"""

import warnings
from collections.abc import AsyncIterator, Iterator

import pytest
from starlette.testclient import TestClient

from woeplanet.spelunker.dependencies.database import Database
from woeplanet.spelunker.server import app

# Suppress ResourceWarning from aiosqlitepool cleanup
warnings.filterwarnings('ignore', message='unclosed database', category=ResourceWarning)


@pytest.fixture(scope='session')
def client() -> Iterator[TestClient]:
    """
    Test client with lifespan management.
    """

    with TestClient(app) as client:
        yield client


@pytest.fixture
async def db(client: TestClient) -> AsyncIterator[Database]:
    """
    Database connection from the app's pool (uses warmed cache).
    """

    _ = client  # ensure lifespan has run
    async with app.state.db_pool.connection() as conn:
        yield Database(conn)
