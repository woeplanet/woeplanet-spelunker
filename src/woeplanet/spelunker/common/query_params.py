"""
WOEplanet Spelunker: common package; query parameters module.
"""

from dataclasses import dataclass
from urllib.parse import urlencode

from starlette.requests import Request

from woeplanet.spelunker.dependencies.database import SearchFilters

VALID_COUNTRY_INCLUDES = frozenset({'deprecated', 'unknown', 'nullisland'})


@dataclass
class ParsedSearchParams:
    """
    Parsed search query parameters.
    """

    filters: SearchFilters
    includes: list[str]
    query_string: str


def parse_search_includes(request: Request) -> ParsedSearchParams:
    """
    Build search filters from the include query param
    """

    raw_includes = request.query_params.getlist(key='include')
    includes = [part for item in raw_includes for part in item.split(',') if part in VALID_COUNTRY_INCLUDES]

    filters = SearchFilters(
        deprecated='deprecated' in includes,
        unknown='unknown' in includes,
        null_island='nullisland' in includes,
    )

    query_string = urlencode([('include', v) for v in includes]) if includes else ''

    return ParsedSearchParams(
        filters=filters,
        includes=includes,
        query_string=query_string,
    )
