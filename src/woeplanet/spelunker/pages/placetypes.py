"""
WOEplanet Spelunker: pages package; placetypes page module
"""

import logging
import time
from http import HTTPStatus

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import HTMLResponse

from woeplanet.spelunker.common.coordinates import extract_coordinates
from woeplanet.spelunker.common.pagination import build_pagination_context
from woeplanet.spelunker.common.path_params import get_path_placetype
from woeplanet.spelunker.common.query_params import parse_filter_params, parse_pagination
from woeplanet.spelunker.config.place_scale import placetype_to_scale
from woeplanet.spelunker.config.placetypes import placetype_by_shortname
from woeplanet.spelunker.dependencies.database import get_db
from woeplanet.spelunker.dependencies.templates import get_templater
from woeplanet.spelunker.pages.random import _random_place

# PROFILING: time import and perf_counter calls below are used for profiling
logger = logging.getLogger(__name__)


async def placetype_facets_endpoint(request: Request) -> HTMLResponse:
    """
    Placetypes page endpoint
    """

    start_total = time.perf_counter()  # PROFILING

    start = time.perf_counter()  # PROFILING
    place = await _random_place(request=request)
    logger.info('_random_place: %.3fs', time.perf_counter() - start)  # PROFILING

    parsed = parse_filter_params(request)

    async with get_db(request=request) as db:
        start = time.perf_counter()  # PROFILING
        total_woeids = await db.get_total_woeids(filters=parsed.filters)
        logger.info('get_total_woeids: %.3fs', time.perf_counter() - start)  # PROFILING

        start = time.perf_counter()  # PROFILING
        placetypes = await db.get_placetype_facets(filters=parsed.filters)
        logger.info('get_placetype_facets: %.3fs', time.perf_counter() - start)  # PROFILING

    start = time.perf_counter()  # PROFILING
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
    logger.info('template render: %.3fs', time.perf_counter() - start)  # PROFILING

    logger.info('placetype_facets_endpoint total: %.3fs', time.perf_counter() - start_total)  # PROFILING
    return HTMLResponse(content)


async def placetype_search_endpoint(request: Request) -> HTMLResponse:
    """
    Placetype page endpoint
    """

    shortname = get_path_placetype(request)
    parsed = parse_filter_params(request)
    pagination = parse_pagination(request)

    async with get_db(request=request) as db:
        placetype = await placetype_by_shortname(db, shortname)
        if not placetype:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f'Placetype {shortname} not found',
            )

        placetype_id = placetype['id']
        total = await db.get_places_by_placetype_count(placetype_id, filters=parsed.filters)
        result = await db.get_places_by_placetype(
            placetype_id,
            filters=parsed.filters,
            after=pagination.after,
            before=pagination.before,
            limit=pagination.limit,
        )

    paging = build_pagination_context(request, result, pagination=pagination, total=total)

    place = result.items[0] if result.items else None
    coords = extract_coordinates(place)

    template = get_templater().get_template('placetype.html.j2')
    template_args = {
        'title': f'Placetype: {placetype["name"]}',
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
        'scale': placetype_to_scale(placetype_id),
        'doc': place,
        'pagination': paging,
    }
    content = await template.render_async(request=request, **template_args)
    return HTMLResponse(content)
