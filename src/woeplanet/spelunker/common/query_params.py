"""
WOEplanet Spelunker: common package; query parameters module.
"""

import re
from dataclasses import dataclass
from http import HTTPStatus
from typing import Annotated, Literal
from urllib.parse import urlencode

from pydantic import BaseModel, Field, ValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request

from woeplanet.spelunker.config.settings import get_settings
from woeplanet.spelunker.dependencies.database import SearchFilters

VALID_COUNTRY_INCLUDES = frozenset({'deprecated', 'unknown', 'nullisland'})
LIMIT_DEFAULT = 10
LIMIT_MAX = 100
MAX_QUERY_LENGTH = 255
MAX_NEARBY_DISTANCE = 100_000

NameType = Literal['any', 'S', 'P', 'V', 'Q', 'A', 'woeid']


class SearchParams(BaseModel):
    """
    Search query parameters with validation.
    """

    q: Annotated[str, Field(max_length=MAX_QUERY_LENGTH)] = ''
    name_type: NameType = 'any'


class NearbyParamsModel(BaseModel):
    """
    Nearby query parameters with validation.
    """

    lat: Annotated[float, Field(ge=-90, le=90)] | None = None
    lng: Annotated[float, Field(ge=-180, le=180)] | None = None
    distance: Annotated[int, Field(gt=0, le=MAX_NEARBY_DISTANCE)] | None = None


class PaginationParamsModel(BaseModel):
    """
    Pagination query parameters with validation.
    """

    after: Annotated[int, Field(gt=0)] | None = None
    before: Annotated[int, Field(gt=0)] | None = None
    limit: Annotated[int, Field(gt=0)] | None = None
    page: Annotated[int, Field(gt=0)] | None = None


@dataclass
class FilterParams:
    """
    Search filtering query parameters.
    """

    filters: SearchFilters
    includes: list[str]
    query_string: str


@dataclass
class PaginationParams:
    """
    Pagination query parameters.
    """

    after: int | None
    before: int | None
    limit: int
    page: int


@dataclass
class NearbyParams:
    """
    Nearby query parameters.
    """

    lat: float | None
    lng: float | None
    distance: int


def parse_nearby_params(request: Request) -> NearbyParams:
    """
    Parse and validate nearby query params.
    """

    settings = get_settings()

    try:
        validated = NearbyParamsModel(
            lat=request.query_params.get('lat'),
            lng=request.query_params.get('lng'),
            distance=request.query_params.get('distance'),
        )
    except ValidationError as exc:
        errors = exc.errors()
        if errors:
            msg = errors[0].get('msg', 'Invalid nearby parameters')
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=msg) from exc

        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Invalid nearby parameters',
        ) from exc

    return NearbyParams(
        lat=validated.lat,
        lng=validated.lng,
        distance=validated.distance if validated.distance else settings.nearby_distance,
    )


def parse_filter_params(request: Request) -> FilterParams:
    """
    Build filter parameters from query parameters
    """

    raw_includes = request.query_params.getlist(key='include')
    includes = [part for item in raw_includes for part in item.split(',') if part in VALID_COUNTRY_INCLUDES]

    filters = SearchFilters(
        deprecated='deprecated' in includes,
        unknown='unknown' in includes,
        null_island='nullisland' in includes,
    )

    query_string = urlencode([('include', v) for v in includes]) if includes else ''

    return FilterParams(
        filters=filters,
        includes=includes,
        query_string=query_string,
    )


def parse_pagination(request: Request) -> PaginationParams:
    """
    Parse and validate pagination query params.
    """

    try:
        validated = PaginationParamsModel(
            after=request.query_params.get('after'),
            before=request.query_params.get('before'),
            limit=request.query_params.get('limit'),
            page=request.query_params.get('page'),
        )
    except ValidationError as exc:
        errors = exc.errors()
        if errors:
            msg = errors[0].get('msg', 'Invalid pagination parameters')
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=msg) from exc

        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Invalid pagination parameters',
        ) from exc

    return PaginationParams(
        after=validated.after,
        before=validated.before,
        limit=min(validated.limit, LIMIT_MAX) if validated.limit else LIMIT_DEFAULT,
        page=validated.page if validated.page else 1,
    )


def parse_search_params(request: Request) -> SearchParams:
    """
    Parse and validate search query parameters.
    """

    try:
        return SearchParams(
            q=request.query_params.get('q', '').strip(),
            name_type=request.query_params.get('name-type', 'any').strip(),
        )
    except ValidationError as exc:
        errors = exc.errors()
        if errors:
            msg = errors[0].get('msg', 'Invalid search parameters')
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=msg) from exc

        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Invalid search parameters',
        ) from exc


def sanitise_name_search_query(query: str) -> str | None:
    """
    Sanitise a query string for use with SQLite FTS5.

    Allows FTS5 operators (AND, OR, NOT, NEAR), quoted phrases, and prefix matching.
    Strips column specifiers and boost operators which aren't applicable.
    Returns None if the query is empty after sanitisation.
    """

    if not query or not query.strip():
        return None

    # Strip column specifier (:) and boost (^) - not applicable to our schema
    sanitised = re.sub(r'[:^]', '', query)

    # Balance quotes - unmatched quotes cause FTS syntax errors
    quote_count = sanitised.count('"')
    if quote_count % 2 != 0:
        last_quote = sanitised.rfind('"')
        sanitised = sanitised[:last_quote] + sanitised[last_quote + 1 :]

    return sanitised.strip() or None
