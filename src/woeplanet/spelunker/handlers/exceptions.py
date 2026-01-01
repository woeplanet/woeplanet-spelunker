"""
WOEplanet Spelunker: handlers package; exception handlers module.
"""

import logging

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import HTMLResponse

from woeplanet.spelunker.dependencies.templates import get_templater

logger = logging.getLogger(__name__)


async def server_error_handler(request: Request, exc: HTTPException) -> HTMLResponse:
    """
    Server error handler
    """

    logger.exception('Server error: %s', request.url, exc_info=exc)

    template = get_templater().get_template('5xx.html.j2')
    template_args = {
        'exc': exc,
    }
    content = await template.render_async(request=request, **template_args, exception=exc)
    return HTMLResponse(content, status_code=exc.status_code)


async def client_error_handler(request: Request, exc: HTTPException) -> HTMLResponse:
    """
    Client error handler
    """

    logger.warning('Client error %d on %s: %s', exc.status_code, request.url, exc.detail)

    template = get_templater().get_template('4xx.html.j2')
    template_args = {
        'exc': exc,
    }
    content = await template.render_async(request=request, **template_args)
    return HTMLResponse(content, status_code=exc.status_code)
