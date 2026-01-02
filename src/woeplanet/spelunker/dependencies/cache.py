"""
WOEplanet Spelunker: dependencies package; caching module.
"""

import functools
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import ParamSpec, TypeVar

from diskcache import Cache, Lock  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')


class CacheHolder:
    """
    Module-level cache holder to avoid global statement.
    """

    cache: Cache | None = None


def init_cache(cache_dir: Path) -> Cache:
    """
    Initialise the disk cache.
    """

    cache_path = cache_dir / 'diskcache'
    logger.info('Initialising disk cache at %s', cache_path)
    CacheHolder.cache = Cache(str(cache_path))
    return CacheHolder.cache


def get_cache() -> Cache | None:
    """
    Get the current cache instance.
    """

    return CacheHolder.cache


def close_cache() -> None:
    """
    Close the disk cache.
    """

    if CacheHolder.cache is not None:
        CacheHolder.cache.close()
        CacheHolder.cache = None


def disk_cache(
    key_builder: Callable[..., str],
    expire: int | None = None,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """
    Decorator for caching async database methods using DiskCache.
    """

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            cache = CacheHolder.cache
            if cache is None:
                return await func(*args, **kwargs)

            key = key_builder(**kwargs)

            result = cache.get(key)
            if result is not None:
                logger.debug('Cache hit for %s', key)
                return result

            lock_key = f'{key}:lock'
            with Lock(cache, lock_key, expire=120):
                result = cache.get(key)
                if result is not None:
                    logger.debug('Cache hit after lock for %s', key)
                    return result

                logger.debug('Cache miss for %s, executing query', key)
                result = await func(*args, **kwargs)
                cache.set(key, result, expire=expire)
                return result

        return wrapper

    return decorator
