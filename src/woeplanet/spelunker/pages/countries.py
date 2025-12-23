"""
WOEplanet Spelunker: pages package; countries page module
"""

import logging
from http import HTTPStatus

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import HTMLResponse

from woeplanet.spelunker.common.pagination import build_pagination_context
from woeplanet.spelunker.common.query_params import parse_filter_params, parse_pagination
from woeplanet.spelunker.config.place_scale import placetype_to_scale
from woeplanet.spelunker.dependencies.database import get_db
from woeplanet.spelunker.dependencies.templates import get_templater
from woeplanet.spelunker.pages.random import _random_place

logger = logging.getLogger(__name__)


async def country_facets_endpoint(request: Request) -> HTMLResponse:
    """
    Countries page endpoint
    """

    place = await _random_place(request=request)
    parsed = parse_filter_params(request)

    async with get_db(request=request) as db:
        total_woeids = await db.get_total_woeids(filters=parsed.filters)
        countries = await db.get_countries_facets(filters=parsed.filters)

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


async def country_search_endpoint(request: Request) -> HTMLResponse:
    """
    Country page endpoint
    """

    iso = request.path_params['iso']
    placetype = request.query_params.get('placetype')
    parsed = parse_filter_params(request)
    pagination = parse_pagination(request)

    async with get_db(request=request) as db:
        buckets = await db.get_placetypes_by_country(iso2=iso, filters=parsed.filters)
        country = await db.get_country_by_iso(iso)

        if not country:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f'Country {iso} not found',
            )

        country_woe_id = country['woe_id']
        total = await db.get_places_by_country_count(
            country_woe_id,
            filters=parsed.filters,
            placetype=placetype,
        )
        result = await db.get_places_by_country(
            country_woe_id,
            filters=parsed.filters,
            placetype=placetype,
            after=pagination.after,
            before=pagination.before,
            limit=pagination.limit,
        )

    paging = build_pagination_context(request, result, pagination=pagination, total=total)

    centroid = None
    bounds = None
    place = result.items[0] if result.items else None
    if place:
        if place.get('lat') and place.get('lng'):
            centroid = [place['lat'], place['lng']]
        if place.get('sw_lat') and place.get('sw_lng') and place.get('ne_lat') and place.get('ne_lng'):
            bounds = [[place['sw_lat'], place['sw_lng']], [place['ne_lat'], place['ne_lng']]]

    title = f'Country: {country["name"]} ({country["iso2"]})'
    if placetype:
        title = f'{placetype.title()} in {country["name"]}'

    template = get_templater().get_template('country.html.j2')
    template_args = {
        'title': title,
        'country': country,
        'placetype': placetype,
        'results': result.items,
        'total': total,
        'includes': parsed.includes,
        'includes_qs': parsed.query_string,
        'map': True,
        'centroid': centroid,
        'bounds': bounds,
        'woeid': place['woe_id'] if place else None,
        'name': place['name'] if place else None,
        'scale': placetype_to_scale(12),
        'doc': place,
        'pagination': paging,
        'buckets': buckets,
    }
    content = await template.render_async(request=request, **template_args)
    return HTMLResponse(content)
