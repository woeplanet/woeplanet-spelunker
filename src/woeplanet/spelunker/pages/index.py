"""
WOEplanet Spelunker: pages package; index page module.
"""

from starlette.requests import Request
from starlette.responses import HTMLResponse

from woeplanet.spelunker.pages.page import render_page


async def index_endpoint(request: Request) -> HTMLResponse:
    """
    Index page endpoint.
    """

    return await render_page(request=request, template_name='index.html.j2', title='Home')
