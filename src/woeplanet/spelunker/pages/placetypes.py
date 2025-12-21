"""
WOEplanet Spelunker: pages package; placetypes page module
"""

import logging

from starlette.requests import Request
from starlette.responses import HTMLResponse

from woeplanet.spelunker.common.query_params import parse_search_includes
from woeplanet.spelunker.config.place_scale import placetype_to_scale
from woeplanet.spelunker.dependencies.database import get_db
from woeplanet.spelunker.dependencies.templates import get_templater
from woeplanet.spelunker.pages.random import _random_place

logger = logging.getLogger(__name__)


async def placetypes_endpoint(request: Request) -> HTMLResponse:
    """
    Placetypes page endpoint
    """

    place = await _random_place(request=request)
    parsed = parse_search_includes(request)

    async with get_db(request=request) as db:
        total_woeids = await db.get_total_woeids(filters=parsed.filters)
        placetypes = await db.get_placetype_facets(filters=parsed.filters)

        logger.debug(placetypes)

    template = get_templater().get_template('placetypes.html.j2')
    template_args = {
        'total': {
            'woeids': total_woeids,
            'placetypes': len(placetypes),
        },
        'includes': parsed.includes,
        'includes_qs': parsed.query_string,
        'map': True,
        'centroid': place.get('centroid'),
        'bounds': place.get('bounds'),
        'title': 'Placetypes',
        'woeid': place.get('woe_id'),
        'name': place.get('name'),
        'scale': placetype_to_scale(int(place.get('placetype_id', 0))),
        'doc': place,
        'placetypes': placetypes,
    }
    content = await template.render_async(request=request, **template_args)
    return HTMLResponse(content)


async def placetype_endpoint(request: Request) -> HTMLResponse:
    """
    Placetype page endpoint
    """

    template = get_templater().get_template('placetype.html.j2')
    content = await template.render_async(request=request)
    return HTMLResponse(content)
