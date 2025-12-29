"""
WOEplanet Spelunker: pages package; places page module
"""

import json
from http import HTTPStatus

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import HTMLResponse

from woeplanet.spelunker.common.languages import language_name
from woeplanet.spelunker.common.pagination import build_offset_pagination_context
from woeplanet.spelunker.common.path_params import get_woeid
from woeplanet.spelunker.common.query_params import parse_filter_params, parse_nearby_params, parse_pagination
from woeplanet.spelunker.config.place_scale import placetype_to_scale
from woeplanet.spelunker.config.placetypes import placetype_by_id
from woeplanet.spelunker.dependencies.database import PlaceFilters, get_db
from woeplanet.spelunker.dependencies.templates import get_templater
from woeplanet.spelunker.pages.random import _random_place


async def place_endpoint(request: Request) -> HTMLResponse:
    """
    Place page endpoint
    """

    woeid = get_woeid(request=request)

    async with get_db(request=request) as db:
        filters = PlaceFilters(
            geometry=True,
            ancestors=True,
            hierarchy=True,
            names=True,
            neighbours=True,
            children=True,
            null_island=False,
            deprecated=False,
            exclude_placetypes=[],
            history=True,
            licensing=True,
        )
        place = await db.get_place_by_id(woeid, filters)

        if not place:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Place with woeid {woeid} not found')

        centroid = None
        if place.get('lat') and place.get('lng'):
            centroid = [place.get('lat'), place.get('lng')]
        bounds = None
        if place.get('sw_lat') and place.get('sw_lng') and place.get('ne_lat') and place.get('ne_lng'):
            bounds = [[place.get('sw_lat'), place.get('sw_lng')], [place.get('ne_lat'), place.get('ne_lng')]]

        name = place.get('name')
        placetype_id = int(place.get('placetype_id', 0))
        template = get_templater().get_template('place.html.j2')
        placetype = await placetype_by_id(db, placetype_id)

        if filters.ancestors:
            ancestor_ids: list[int] = place.get('ancestors') or []
            place['ancestors'] = await db.inflate_place_ids(ancestor_ids)

        if filters.children:
            child_ids: list[int] = place.get('children') or []
            place['children'] = await db.inflate_place_ids(child_ids)

        if filters.hierarchy:
            hierarchy = place.get('hierarchy')
            place['hierarchy'] = hierarchy

        if filters.neighbours:
            neighbour_ids: list[int] = place.get('neighbours') or []
            place['neighbours'] = await db.inflate_place_ids(neighbour_ids)

        template_args = {
            'map': True,
            'centroid': centroid,
            'bounds': bounds,
            'title': f'WOEID {woeid} ({name if name else "Unknown"})',
            'woeid': place.get('woe_id'),
            'name': place.get('name'),
            'lang': language_name(str(place.get('language', 'UNK'))),
            'scale': placetype_to_scale(placetype_id),
            'doc': place,
            'placetype': placetype,
        }
        content = await template.render_async(request=request, **template_args)
        return HTMLResponse(content)


async def place_map_endpoint(request: Request) -> HTMLResponse:
    """
    Place map page endpoint
    """

    woeid = get_woeid(request=request)

    async with get_db(request=request) as db:
        filters = PlaceFilters(
            centroid=True,
            bounding_box=True,
            geometry=True,
            ancestors=False,
            hierarchy=False,
            names=False,
            neighbours=False,
            children=False,
            null_island=False,
            deprecated=False,
            exclude_placetypes=[],
            history=False,
            licensing=False,
        )
        place = await db.get_place_by_id(woeid, filters)

        if not place:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Place with woeid {woeid} not found')

        centroid = None
        if place.get('lat') and place.get('lng'):
            centroid = [place.get('lat'), place.get('lng')]
        bounds = None
        if place.get('sw_lat') and place.get('sw_lng') and place.get('ne_lat') and place.get('ne_lng'):
            bounds = [[place.get('sw_lat'), place.get('sw_lng')], [place.get('ne_lat'), place.get('ne_lng')]]

        geom = place.get('geom')
        geojson = None
        if geom:
            geojson = {
                'type': 'Feature',
                'properties': {
                    'woe_id': place.get('woe_id'),
                    'name': place.get('name'),
                    'placetype': place.get('placetype_name'),
                },
                'geometry': json.loads(geom) if isinstance(geom, str) else geom,
            }
        elif bounds:
            sw_lat, sw_lng = bounds[0]
            ne_lat, ne_lng = bounds[1]
            geojson = {
                'type': 'Feature',
                'properties': {
                    'woe_id': place.get('woe_id'),
                    'name': place.get('name'),
                    'placetype': place.get('placetype_name'),
                },
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [
                        [
                            [sw_lng, sw_lat],
                            [ne_lng, sw_lat],
                            [ne_lng, ne_lat],
                            [sw_lng, ne_lat],
                            [sw_lng, sw_lat],
                        ]
                    ],
                },
            }

        name = place.get('name')
        placetype_id = int(place.get('placetype_id', 0))
        template = get_templater().get_template('map.html.j2')

        template_args = {
            'map': True,
            'centroid': centroid,
            'bounds': bounds,
            'geojson': json.dumps(geojson) if geojson else None,
            'title': f'Map: {name if name else "Unknown"} ({woeid})',
            'woeid': place.get('woe_id'),
            'name': place.get('name'),
            'scale': placetype_to_scale(placetype_id),
            'doc': place,
        }
        content = await template.render_async(request=request, **template_args)
        return HTMLResponse(content)


async def place_nearby_endpoint(request: Request) -> HTMLResponse:
    """
    Place nearby page endpoint - finds places near a given WOE ID's centroid
    """

    woeid = get_woeid(request=request)
    nearby_params = parse_nearby_params(request)
    filter_params = parse_filter_params(request)
    pagination = parse_pagination(request)
    offset = (pagination.page - 1) * pagination.limit

    async with get_db(request=request) as db:
        place_filters = PlaceFilters(
            geometry=False,
            ancestors=False,
            hierarchy=False,
            names=False,
            neighbours=False,
            children=False,
            null_island=False,
            deprecated=False,
            exclude_placetypes=[],
            history=False,
            licensing=False,
        )
        place = await db.get_place_by_id(woeid, place_filters)

        if not place:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Place with woeid {woeid} not found')

        lat = place.get('lat')
        lng = place.get('lng')
        distance = nearby_params.distance
        template = get_templater().get_template('nearby-results.html.j2')

        if lat is None or lng is None:
            template_args = {
                'map': False,
                'title': f'Near {place.get("name")}',
                'woeid': woeid,
                'name': place.get('name'),
                'scale': placetype_to_scale(int(place.get('placetype_id', 0))),
                'doc': place,
                'results': [],
                'distance': distance,
                'includes': filter_params.includes,
                'includes_qs': filter_params.query_string,
                'total': 0,
                'no_centroid': True,
            }
            content = await template.render_async(request=request, **template_args)
            return HTMLResponse(content)

        total = await db.get_places_near_centroid_count(
            lat=lat,
            lng=lng,
            distance=distance,
            filters=filter_params.filters,
        )
        result = await db.get_places_near_centroid(
            lat=lat,
            lng=lng,
            distance=distance,
            filters=filter_params.filters,
            limit=pagination.limit,
            offset=offset,
        )

        paging = build_offset_pagination_context(request, result, pagination=pagination, total=total)

        template_args = {
            'map': True,
            'centroid': [lat, lng],
            'title': f'Near {place.get("name")}',
            'woeid': woeid,
            'name': place.get('name'),
            'scale': placetype_to_scale(int(place.get('placetype_id', 0))),
            'doc': place,
            'results': result.items,
            'lat': lat,
            'lng': lng,
            'distance': distance,
            'includes': filter_params.includes,
            'includes_qs': filter_params.query_string,
            'pagination': paging,
            'total': total,
        }
        content = await template.render_async(request=request, **template_args)
        return HTMLResponse(content)


async def nearby_endpoint(request: Request) -> HTMLResponse:
    """
    Nearby page endpoint
    """

    nearby_params = parse_nearby_params(request)

    if nearby_params.lat is None or nearby_params.lng is None:
        place = await _random_place(request=request)
        template = get_templater().get_template('nearby.html.j2')
        template_args = {
            'map': True,
            'centroid': place.get('centroid'),
            'bounds': place.get('bounds'),
            'title': 'Nearby',
            'woeid': place.get('woe_id'),
            'name': place.get('name'),
            'scale': placetype_to_scale(int(place.get('placetype_id', 0))),
            'doc': place,
        }
        content = await template.render_async(request=request, **template_args)
        return HTMLResponse(content)

    filter_params = parse_filter_params(request)
    pagination = parse_pagination(request)
    offset = (pagination.page - 1) * pagination.limit

    async with get_db(request=request) as db:
        total = await db.get_places_near_centroid_count(
            lat=nearby_params.lat,
            lng=nearby_params.lng,
            distance=nearby_params.distance,
            filters=filter_params.filters,
        )
        result = await db.get_places_near_centroid(
            lat=nearby_params.lat,
            lng=nearby_params.lng,
            distance=nearby_params.distance,
            filters=filter_params.filters,
            limit=pagination.limit,
            offset=offset,
        )

        paging = build_offset_pagination_context(request, result, pagination=pagination, total=total)

        first_place = result.items[0] if result.items else None
        template = get_templater().get_template('nearby-results.html.j2')
        template_args = {
            'map': True,
            'centroid': [nearby_params.lat, nearby_params.lng],
            'title': 'Nearby',
            'woeid': first_place['woe_id'] if first_place else 0,
            'name': first_place['name'] if first_place else 'Nearby',
            'scale': placetype_to_scale(first_place['placetype_id']) if first_place else 15,
            'doc': first_place if first_place else {},
            'results': result.items,
            'lat': nearby_params.lat,
            'lng': nearby_params.lng,
            'distance': nearby_params.distance,
            'includes': filter_params.includes,
            'includes_qs': filter_params.query_string,
            'pagination': paging,
            'total': total,
        }
        content = await template.render_async(request=request, **template_args)
        return HTMLResponse(content)
