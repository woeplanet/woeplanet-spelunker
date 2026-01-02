"""
WOEplanet Spelunker: pages package; licenses page module
"""

import logging
from http import HTTPStatus

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import HTMLResponse

from woeplanet.spelunker.config.place_scale import placetype_to_scale
from woeplanet.spelunker.dependencies.database import get_db
from woeplanet.spelunker.dependencies.templates import get_templater
from woeplanet.spelunker.pages.random import _random_place

logger = logging.getLogger(__name__)


async def licenses_endpoint(request: Request) -> HTMLResponse:
    """
    Licenses page endpoint
    """

    place = await _random_place(request=request)

    async with get_db(request=request) as db:
        licenses = await db.get_licenses()
        if not licenses:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail='Failed to get licenses from database',
            )

    template = get_templater().get_template('licenses.html.j2')
    template_args = {
        'map': True,
        'centroid': place.get('centroid'),
        'bounds': place.get('bounds'),
        'title': 'Licenses',
        'woeid': place.get('woe_id'),
        'name': place.get('name'),
        'scale': placetype_to_scale(int(place.get('placetype_id', 0))),
        'doc': place,
        'licenses': licenses,
    }
    content = await template.render_async(request=request, **template_args)
    return HTMLResponse(content)
