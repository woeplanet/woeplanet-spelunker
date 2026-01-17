"""
WOEplanet Spelunker: server module
"""

import multiprocessing
from http import HTTPStatus

import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware

from woeplanet.spelunker.config.settings import get_settings
from woeplanet.spelunker.handlers.exceptions import client_error_handler, server_error_handler
from woeplanet.spelunker.handlers.lifespan import lifespan
from woeplanet.spelunker.middleware.timing import TimingMiddleware
from woeplanet.spelunker.routers.routes import routes

settings = get_settings()
handlers = {
    HTTPStatus.BAD_REQUEST.value: client_error_handler,
    HTTPStatus.NOT_FOUND.value: client_error_handler,
    HTTPStatus.INTERNAL_SERVER_ERROR.value: server_error_handler,
}
middleware = [
    Middleware(TimingMiddleware),  # type: ignore[arg-type]
]
app = Starlette(
    debug=settings.woeplanet_log_level == 'debug',
    routes=routes(),
    exception_handlers=handlers,  # type: ignore[arg-type]
    lifespan=lifespan,
    middleware=middleware,
)


def main() -> None:
    """
    Server entrypoint
    """

    workers = multiprocessing.cpu_count() * 2 + 1
    uvicorn.run(
        'woeplanet.spelunker.server:app',
        host=settings.woeplanet_host,
        port=settings.woeplanet_port,
        workers=workers,
        log_level=settings.woeplanet_log_level,
        log_config=settings.woeplanet_logging_config.as_posix(),
        proxy_headers=True,
        server_header=False,
    )


if __name__ == '__main__':
    main()
