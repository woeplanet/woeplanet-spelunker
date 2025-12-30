"""
WOEplanet Spelunker: pages package; about page module.
"""

from starlette.requests import Request
from starlette.responses import HTMLResponse

from woeplanet.spelunker.pages.page import render_page


async def about_endpoint(request: Request) -> HTMLResponse:
    """
    About page endpoint.
    """

    return await render_page(request=request, template_name='about.html.j2', title='About')
