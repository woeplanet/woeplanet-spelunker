"""
WOEplanet Spelunker: pages package; countries page module
"""

import logging
from http import HTTPStatus

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import HTMLResponse

from woeplanet.spelunker.common.coordinates import extract_coordinates
from woeplanet.spelunker.common.pagination import build_pagination_context
from woeplanet.spelunker.common.path_params import get_path_iso_code
from woeplanet.spelunker.common.query_params import parse_filter_params, parse_pagination, parse_placetype_filter
from woeplanet.spelunker.config.place_scale import placetype_to_scale
from woeplanet.spelunker.config.placetypes import PLACETYPE_COUNTRY, PLACETYPE_UNKNOWN
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
        'scale': placetype_to_scale(int(place.get('placetype_id', PLACETYPE_UNKNOWN))),
        'doc': place,
    }
    content = await template.render_async(request=request, **template_args)
    return HTMLResponse(content)


async def country_search_endpoint(request: Request) -> HTMLResponse:
    """
    Country page endpoint
    """

    iso = get_path_iso_code(request)
    placetype = parse_placetype_filter(request)
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
            country_woe_id=country_woe_id,
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

    place = result.items[0] if result.items else None
    coords = extract_coordinates(place)

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
        'centroid': coords.centroid,
        'bounds': coords.bounds,
        'woeid': place['woe_id'] if place else None,
        'name': place['name'] if place else None,
        'scale': placetype_to_scale(PLACETYPE_COUNTRY),
        'doc': place,
        'pagination': paging,
        'buckets': buckets,
    }
    content = await template.render_async(request=request, **template_args)
    return HTMLResponse(content)
