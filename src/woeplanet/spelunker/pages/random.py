"""
WOEplanet Spelunker: pages package; random page module.
"""

from http import HTTPStatus
from typing import Any

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse

from woeplanet.spelunker.common.coordinates import extract_coordinates
from woeplanet.spelunker.dependencies.database import PlaceFilters, get_db


async def random_endpoint(request: Request) -> RedirectResponse:
    """
    Random page endpoint
    """

    async with get_db(request=request) as db:
        filters = PlaceFilters(
            geometry=False, ancestors=False, hierarchy=False, names=False, neighbours=False, children=False
        )
        random_place = await db.get_random_place(filters)

        if not random_place:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail='Failed to get random place from database'
            )

        place = await db.get_place_by_id(random_place['woe_id'], filters)

        if not place:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f'Failed to get place by id {random_place["woe_id"]}',
            )

        return RedirectResponse(request.url_for('place_endpoint', woeid=random_place['woe_id']))


async def _random_place(request: Request) -> dict[str, Any]:
    """
    Helper function to get a random place for display in the sidebar
    """

    async with get_db(request=request) as db:
        filters = PlaceFilters(
            geometry=False, ancestors=False, hierarchy=False, names=False, neighbours=False, children=False
        )
        random_place = await db.get_random_place(filters)

        if not random_place:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail='Failed to get random place from database'
            )

        place = await db.get_place_by_id(random_place['woe_id'], filters)

        if not place:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f'Failed to get place by id {random_place["woe_id"]}',
            )

        coords = extract_coordinates(place)
        place['centroid'] = coords.centroid
        place['bounds'] = coords.bounds

        return place
