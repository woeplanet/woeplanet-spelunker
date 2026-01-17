"""
WOEplanet Spelunker: common package; profiling module.
"""

import functools
import logging
import time
from collections.abc import Awaitable, Callable

from woeplanet.spelunker.config.settings import get_settings

logger = logging.getLogger(__name__)


def is_profiling_enabled() -> bool:
    """
    Are we profiling?
    """

    return get_settings().woeplanet_log_level == 'debug'


def profile_async[T, **P](func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    """
    Decorator to profile async functions
    """

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        if not is_profiling_enabled():
            return await func(*args, **kwargs)

        start = time.perf_counter()
        try:
            return await func(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - start
            logger.debug('%s: %.3fs', func.__qualname__, elapsed)

    return wrapper


def profile_sync[T, **P](func: Callable[P, T]) -> Callable[P, T]:
    """
    Decorator to profile sync functions
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        if not is_profiling_enabled():
            return func(*args, **kwargs)

        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - start
            logger.debug('%s: %.3fs', func.__qualname__, elapsed)

    return wrapper
