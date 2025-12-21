"""
WOEplanet Spelunker: handlers package; lifespan module.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from starlette.applications import Starlette

from woeplanet.spelunker.config.settings import get_settings
from woeplanet.spelunker.dependencies.database import init_pool

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    """
    ASGI lifespan context manager
    """

    logger.info('Worker starting up')
    settings = get_settings()
    app.state.db_pool = await init_pool(settings.db_path, settings.geom_db_path)
    yield
    await app.state.db_pool.close()
    logger.info('Worker shutting down')
