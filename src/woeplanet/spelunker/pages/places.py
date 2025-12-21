"""
WOEplanet Spelunker: pages package; places page module
"""

from http import HTTPStatus

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import HTMLResponse

from woeplanet.spelunker.common.languages import language_name
from woeplanet.spelunker.common.path_params import get_woeid
from woeplanet.spelunker.config.place_scale import placetype_to_scale
from woeplanet.spelunker.config.placetypes import placetype_by_id
from woeplanet.spelunker.dependencies.database import PlaceFilters, get_db
from woeplanet.spelunker.dependencies.templates import get_templater


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

    template = get_templater().get_template('place_map.html.j2')
    content = await template.render_async(request=request)
    return HTMLResponse(content)


async def place_nearby_endpoint(request: Request) -> HTMLResponse:
    """
    Place nearby page endpoint
    """

    template = get_templater().get_template('place_nearby.html.j2')
    content = await template.render_async(request=request)
    return HTMLResponse(content)


async def nearby_endpoint(request: Request) -> HTMLResponse:
    """
    Nearby page endpoint
    """

    template = get_templater().get_template('nearby.html.j2')
    content = await template.render_async(request=request)
    return HTMLResponse(content)
