"""
WOEplanet Spelunker: pages package; countries page module
"""

from starlette.requests import Request
from starlette.responses import HTMLResponse

from woeplanet.spelunker.common.query_params import parse_search_includes
from woeplanet.spelunker.config.place_scale import placetype_to_scale
from woeplanet.spelunker.dependencies.database import get_db
from woeplanet.spelunker.dependencies.templates import get_templater
from woeplanet.spelunker.pages.random import _random_place


async def countries_endpoint(request: Request) -> HTMLResponse:
    """
    Countries page endpoint
    """

    place = await _random_place(request=request)
    parsed = parse_search_includes(request)

    async with get_db(request=request) as db:
        total_woeids = await db.get_total_woeids(filters=parsed.filters)
        countries = await db.get_countries(filters=parsed.filters)

    template = get_templater().get_template('countries.html.j2')
    template_args = {
        'total': {
            'woeids': total_woeids,
            'countries': len(countries),
        },
        'countries': countries,
        'includes': parsed.includes,
        'includes_qs': parsed.query_string,
        'map': True,
        'centroid': place.get('centroid'),
        'bounds': place.get('bounds'),
        'title': 'Countries',
        'woeid': place.get('woe_id'),
        'iso': place.get('iso', 'GB'),
        'nearby': place.get('woe_id'),
        'name': place.get('name'),
        'scale': placetype_to_scale(int(place.get('placetype_id', 0))),
        'doc': place,
    }
    content = await template.render_async(request=request, **template_args)
    return HTMLResponse(content)


async def country_endpoint(request: Request) -> HTMLResponse:
    """
    Country page endpoint
    """

    template = get_templater().get_template('country.html.j2')
    content = await template.render_async(request=request)
    return HTMLResponse(content)
