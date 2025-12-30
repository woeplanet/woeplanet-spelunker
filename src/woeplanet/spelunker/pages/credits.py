"""
WOEplanet Spelunker: pages package; credits page module.
"""

from starlette.requests import Request
from starlette.responses import HTMLResponse

from woeplanet.spelunker.pages.page import render_page


async def credits_endpoint(request: Request) -> HTMLResponse:
    """
    Credits page endpoint.
    """

    return await render_page(request=request, template_name='credits.html.j2', title='Credits')
