"""
WOEplanet Spelunker: pages package; search page module
"""

import logging
from http import HTTPStatus

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response

from woeplanet.spelunker.common.coordinates import extract_coordinates
from woeplanet.spelunker.common.fts import sanitise_name_search_query
from woeplanet.spelunker.common.pagination import build_pagination_context
from woeplanet.spelunker.common.query_params import parse_filter_params, parse_pagination, parse_search_params
from woeplanet.spelunker.config.place_scale import placetype_to_scale
from woeplanet.spelunker.dependencies.database import get_db
from woeplanet.spelunker.dependencies.templates import get_templater
from woeplanet.spelunker.pages.random import _random_place

logger = logging.getLogger(__name__)


async def search_endpoint(request: Request) -> Response:
    """
    Search page endpoint
    """

    search = parse_search_params(request)

    if search.q:
        if search.name_type == 'woeid':
            return await _do_woeid_search(search.q)

        return await _do_name_search(request, search.q, search.name_type)

    return await _render_search_form(request, search.q, search.name_type)


async def _do_woeid_search(q: str) -> Response:
    """
    Handle WOE ID search - redirect to place page.
    """

    try:
        woeid = int(q)
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='WOE ID must be a valid integer',
        ) from exc

    return RedirectResponse(url=f'/id/{woeid}', status_code=HTTPStatus.FOUND)


async def _do_name_search(request: Request, q: str, name_type: str) -> HTMLResponse:
    """
    Handle free text name search with optional name_type filter.
    """

    sanitised_query = sanitise_name_search_query(q)
    if not sanitised_query:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Invalid search query',
        )

    parsed = parse_filter_params(request)
    pagination = parse_pagination(request)

    async with get_db(request=request) as db:
        total = await db.search_places_fts_count(
            sanitised_query,
            name_type=name_type if name_type != 'any' else None,
            filters=parsed.filters,
        )
        result = await db.search_places_fts(
            sanitised_query,
            name_type=name_type if name_type != 'any' else None,
            filters=parsed.filters,
            after=pagination.after,
            before=pagination.before,
            limit=pagination.limit,
        )

    paging = build_pagination_context(request, result, pagination=pagination, total=total)

    place = result.items[0] if result.items else None
    coords = extract_coordinates(place)

    template = get_templater().get_template('search-results.html.j2')
    template_args = {
        'title': f'Search: {q}',
        'q': q,
        'search_type': name_type,
        'results': result.items,
        'total': total,
        'includes': parsed.includes,
        'includes_qs': parsed.query_string,
        'map': bool(coords.centroid),
        'centroid': coords.centroid,
        'bounds': coords.bounds,
        'woeid': place['woe_id'] if place else None,
        'name': place['name'] if place else None,
        'scale': placetype_to_scale(12),
        'doc': place,
        'pagination': paging,
    }
    content = await template.render_async(request=request, **template_args)
    return HTMLResponse(content)


async def _render_search_form(request: Request, q: str, name_type: str) -> HTMLResponse:
    """
    Render the search form page.
    """

    place = await _random_place(request=request)
    template = get_templater().get_template('search.html.j2')
    template_args = {
        'map': True,
        'centroid': place.get('centroid'),
        'bounds': place.get('bounds'),
        'title': 'Search',
        'woeid': place.get('woe_id'),
        'iso': place.get('iso', 'GB'),
        'nearby': place.get('woe_id'),
        'name': place.get('name'),
        'scale': placetype_to_scale(int(place.get('placetype_id', 0))),
        'doc': place,
        'q': q,
        'search_type': name_type,
    }
    content = await template.render_async(request=request, **template_args)
    return HTMLResponse(content)
