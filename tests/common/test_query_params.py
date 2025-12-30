"""
WOEplanet Spelunker: tests package; query parameters tests.
"""

from http import HTTPStatus
from unittest.mock import MagicMock

import pytest
from starlette.datastructures import QueryParams
from starlette.exceptions import HTTPException

from woeplanet.spelunker.common.query_params import (
    LIMIT_DEFAULT,
    LIMIT_MAX,
    parse_filter_params,
    parse_nearby_params,
    parse_pagination,
    parse_search_params,
)

FIRST_PAGE = 1
FIFTH_PAGE = 5
CUSTOM_LIMIT = 25
CURSOR_AFTER = 1000
CURSOR_BEFORE = 2000
CUSTOM_DISTANCE = 10000


class TestParseFilterParams:
    """
    Tests for the parse_filter_params function.
    """

    def test_no_includes_returns_defaults(self) -> None:
        """
        No include params should return default filters.
        """

        request = MagicMock()
        request.query_params = QueryParams('')

        result = parse_filter_params(request)

        assert result.filters.deprecated is False
        assert result.filters.unknown is False
        assert result.filters.null_island is False
        assert result.includes == []
        assert result.query_string == ''

    def test_deprecated_include(self) -> None:
        """
        Include deprecated should set filter.
        """

        request = MagicMock()
        request.query_params = QueryParams('include=deprecated')

        result = parse_filter_params(request)

        assert result.filters.deprecated is True
        assert 'deprecated' in result.includes

    def test_multiple_includes(self) -> None:
        """
        Multiple includes should all be set.
        """

        request = MagicMock()
        request.query_params = QueryParams('include=deprecated&include=nullisland')

        result = parse_filter_params(request)

        assert result.filters.deprecated is True
        assert result.filters.null_island is True
        assert 'deprecated' in result.includes
        assert 'nullisland' in result.includes

    def test_comma_separated_includes(self) -> None:
        """
        Comma-separated includes should be parsed.
        """

        request = MagicMock()
        request.query_params = QueryParams('include=deprecated,unknown')

        result = parse_filter_params(request)

        assert result.filters.deprecated is True
        assert result.filters.unknown is True

    def test_invalid_includes_ignored(self) -> None:
        """
        Invalid include values should be ignored.
        """

        request = MagicMock()
        request.query_params = QueryParams('include=invalid')

        result = parse_filter_params(request)

        assert result.includes == []


class TestParsePagination:
    """
    Tests for the parse_pagination function.
    """

    def test_defaults(self) -> None:
        """
        No params should return defaults.
        """

        request = MagicMock()
        request.query_params = QueryParams('')

        result = parse_pagination(request)

        assert result.after is None
        assert result.before is None
        assert result.limit == LIMIT_DEFAULT
        assert result.page == FIRST_PAGE

    def test_custom_limit(self) -> None:
        """
        Custom limit should be parsed.
        """

        request = MagicMock()
        request.query_params = QueryParams(f'limit={CUSTOM_LIMIT}')

        result = parse_pagination(request)

        assert result.limit == CUSTOM_LIMIT

    def test_limit_capped_at_max(self) -> None:
        """
        Limit should be capped at max value.
        """

        request = MagicMock()
        request.query_params = QueryParams(f'limit={LIMIT_MAX + 100}')

        result = parse_pagination(request)

        assert result.limit == LIMIT_MAX

    def test_after_cursor(self) -> None:
        """
        After cursor should be parsed.
        """

        request = MagicMock()
        request.query_params = QueryParams(f'after={CURSOR_AFTER}')

        result = parse_pagination(request)

        assert result.after == CURSOR_AFTER

    def test_before_cursor(self) -> None:
        """
        Before cursor should be parsed.
        """

        request = MagicMock()
        request.query_params = QueryParams(f'before={CURSOR_BEFORE}')

        result = parse_pagination(request)

        assert result.before == CURSOR_BEFORE

    def test_page_number(self) -> None:
        """
        Page number should be parsed.
        """

        request = MagicMock()
        request.query_params = QueryParams(f'page={FIFTH_PAGE}')

        result = parse_pagination(request)

        assert result.page == FIFTH_PAGE


class TestParseNearbyParams:
    """
    Tests for the parse_nearby_params function.
    """

    def test_no_coords_returns_none(self) -> None:
        """
        No coords should return None for lat/lng.
        """

        request = MagicMock()
        request.query_params = QueryParams('')

        result = parse_nearby_params(request)

        assert result.lat is None
        assert result.lng is None

    def test_coords_parsed(self) -> None:
        """
        Coordinates should be parsed as floats.
        """

        request = MagicMock()
        request.query_params = QueryParams('lat=51.5074&lng=-0.1278')

        result = parse_nearby_params(request)

        assert result.lat == pytest.approx(51.5074)
        assert result.lng == pytest.approx(-0.1278)

    def test_custom_distance(self) -> None:
        """
        Custom distance should be parsed.
        """

        request = MagicMock()
        request.query_params = QueryParams(f'lat=51.5&lng=-0.1&distance={CUSTOM_DISTANCE}')

        result = parse_nearby_params(request)

        assert result.distance == CUSTOM_DISTANCE


class TestParseSearchParams:
    """
    Tests for the parse_search_params function.
    """

    def test_empty_query(self) -> None:
        """
        Empty query should return empty string.
        """

        request = MagicMock()
        request.query_params = QueryParams('')

        result = parse_search_params(request)

        assert result.q == ''
        assert result.name_type == 'any'

    def test_query_string(self) -> None:
        """
        Query string should be parsed.
        """

        request = MagicMock()
        request.query_params = QueryParams('q=London')

        result = parse_search_params(request)

        assert result.q == 'London'

    def test_query_stripped(self) -> None:
        """
        Query should be stripped of whitespace.
        """

        request = MagicMock()
        request.query_params = QueryParams('q=  London  ')

        result = parse_search_params(request)

        assert result.q == 'London'

    def test_name_type_filter(self) -> None:
        """
        Name type filter should be parsed.
        """

        request = MagicMock()
        request.query_params = QueryParams('q=London&name-type=P')

        result = parse_search_params(request)

        assert result.name_type == 'P'

    def test_woeid_name_type(self) -> None:
        """
        WOEID name type should be parsed.
        """

        request = MagicMock()
        request.query_params = QueryParams('q=44418&name-type=woeid')

        result = parse_search_params(request)

        assert result.name_type == 'woeid'

    def test_query_too_long_raises(self) -> None:
        """
        Query exceeding max length should raise HTTPException.
        """

        request = MagicMock()
        request.query_params = QueryParams(f'q={"x" * 300}')

        with pytest.raises(HTTPException) as exc_info:
            parse_search_params(request)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
