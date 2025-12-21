"""
WOEplanet Spelunker: pages package; credits page module
"""

import logging

from starlette.requests import Request
from starlette.responses import HTMLResponse

from woeplanet.spelunker.config.place_scale import placetype_to_scale
from woeplanet.spelunker.dependencies.templates import get_templater
from woeplanet.spelunker.pages.random import _random_place

logger = logging.getLogger(__name__)


async def credits_endpoint(request: Request) -> HTMLResponse:
    """
    Credits page endpoint
    """

    place = await _random_place(request=request)
    template = get_templater().get_template('credits.html.j2')
    template_args = {
        'map': True,
        'centroid': place.get('centroid'),
        'bounds': place.get('bounds'),
        'title': 'Credits',
        'woeid': place.get('woe_id'),
        'iso': place.get('iso', 'GB'),
        'nearby': place.get('woe_id'),
        'name': place.get('name'),
        'scale': placetype_to_scale(int(place.get('placetype_id', 0))),
        'doc': place,
    }
    content = await template.render_async(request=request, **template_args)
    return HTMLResponse(content)
