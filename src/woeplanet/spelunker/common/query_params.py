"""
WOEplanet Spelunker: common package; query parameters module.
"""

from dataclasses import dataclass
from http import HTTPStatus
from typing import Annotated, Literal
from urllib.parse import urlencode

from pydantic import BaseModel, Field, ValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request

from woeplanet.spelunker.dependencies.database import SearchFilters

VALID_COUNTRY_INCLUDES = frozenset({'deprecated', 'unknown', 'nullisland'})
LIMIT_DEFAULT = 10
LIMIT_MAX = 100
MAX_QUERY_LENGTH = 255

NameType = Literal['any', 'S', 'P', 'V', 'Q', 'A', 'woeid']


class SearchParams(BaseModel):
    """
    Search query parameters with validation.
    """

    q: Annotated[str, Field(max_length=MAX_QUERY_LENGTH)] = ''
    name_type: NameType = 'any'


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
    Parse pagination query params.
    """

    after = request.query_params.get('after')
    before = request.query_params.get('before')
    limit = request.query_params.get('limit')
    page = request.query_params.get('page')

    return PaginationParams(
        after=int(after) if after else None,
        before=int(before) if before else None,
        limit=min(int(limit) if limit else LIMIT_DEFAULT, LIMIT_MAX),
        page=int(page) if page else 1,
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
