"""
WOEplanet Spelunker: middleware package; timing middleware module.
"""

import time

from starlette.applications import Starlette
from starlette.datastructures import MutableHeaders
from starlette.types import Message, Receive, Scope, Send


class TimingMiddleware:
    """
    ASGI middleware to report elapsed page load time as the X-Page-Load-Time header
    """

    def __init__(self, app: Starlette) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope['type'] != 'http':
            return await self._app(scope, receive, send)

        async def send_wrapper(message: Message) -> None:
            if message['type'] == 'http.response.start':
                end_time = time.perf_counter()
                elapsed = end_time - start_time
                headers = MutableHeaders(scope=message)
                headers.append('X-Page-Load-Time', f'{elapsed:0.4f}s')

            await send(message)

        start_time = time.perf_counter()
        await self._app(scope, receive, send_wrapper)

        return None
