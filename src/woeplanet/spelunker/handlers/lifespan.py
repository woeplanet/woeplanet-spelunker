"""
WOEplanet Spelunker: handlers package; lifespan module.
"""

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from diskcache import Lock  # type: ignore[import-untyped]
from starlette.applications import Starlette

from woeplanet.spelunker.config.settings import get_settings
from woeplanet.spelunker.dependencies.cache import close_cache, get_cache, init_cache
from woeplanet.spelunker.dependencies.database import SearchFilters, get_db, init_pool

logger = logging.getLogger(__name__)

PREWARM_FILTERS = [
    SearchFilters(deprecated=False, unknown=False, null_island=False),
]


async def prewarm_cache(app: Starlette) -> None:
    """
    Pre-warm the cache with expensive queries.

    Uses blocking lock so workers wait, then checks if cache is already warm.
    """

    cache = get_cache()
    if cache is None:
        return

    with Lock(cache, 'prewarm-lock', expire=300):
        warm_key = 'cache-warm'
        if cache.get(warm_key):
            logger.info('Cache already warm, skipping')
            return

        start = time.perf_counter()
        logger.info('Pre-warming cache')

        async with get_db(app=app) as db:
            for filters in PREWARM_FILTERS:
                await db.get_total_woeids(filters=filters)
                await db.get_placetype_facets(filters=filters)
                await db.get_countries_facets(filters=filters)

            await db.get_placetypes()

        cache.set(warm_key, 1, expire=3600)
        logger.info('Cache pre-warm complete in %.3fs', time.perf_counter() - start)


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    """
    ASGI lifespan context manager
    """

    logger.info('Worker starting up')
    settings = get_settings()
    app.state.db_pool = await init_pool(settings.woeplanet_db_path, settings.woeplanet_geom_db_path)
    init_cache(settings.woeplanet_cache_dir)
    await prewarm_cache(app)
    logger.info('Worker ready')
    yield
    close_cache()
    await app.state.db_pool.close()
    logger.info('Worker shutting down')
