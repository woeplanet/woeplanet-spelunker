"""
WOEplanet Spelunker: tests package; pagination tests.
"""

from unittest.mock import MagicMock

from starlette.datastructures import URL

from woeplanet.spelunker.common.pagination import (
    build_offset_pagination_context,
    build_pagination_context,
)
from woeplanet.spelunker.common.query_params import PaginationParams
from woeplanet.spelunker.dependencies.database import PaginatedResult

DEFAULT_LIMIT = 10
FIRST_PAGE = 1
SECOND_PAGE = 2
THIRD_PAGE = 3
FOURTH_PAGE = 4
FIFTH_PAGE = 5
TENTH_PAGE = 10

TOTAL_ZERO = 0
TOTAL_FIFTY = 50
TOTAL_NINETY_FIVE = 95
TOTAL_HUNDRED = 100

EXPECTED_PAGES_TEN = 10

WOE_ID_FIRST = 1
WOE_ID_SECOND = 2
WOE_ID_TEN = 10
WOE_ID_TWENTY = 20
WOE_ID_EIGHTY = 80
WOE_ID_NINETY = 90
WOE_ID_HUNDRED = 100

CURSOR_AFTER_FIVE = 5


def make_request(url: str = 'http://test/path') -> MagicMock:
    """
    Create a mock request with the given URL.
    """

    request = MagicMock()
    request.url = URL(url)
    return request


class TestBuildPaginationContext:
    """
    Tests for the build_pagination_context function (cursor-based).
    """

    def test_empty_result_no_pagination(self) -> None:
        """
        Empty result should have no pagination URLs.
        """

        request = make_request()
        result = PaginatedResult(items=[], has_more=False)
        pagination = PaginationParams(after=None, before=None, limit=DEFAULT_LIMIT, page=FIRST_PAGE)

        context = build_pagination_context(request, result, pagination=pagination, total=TOTAL_ZERO)

        assert context.urls.prev is None
        assert context.urls.next is None
        assert context.page == FIRST_PAGE
        assert context.pages == FIRST_PAGE

    def test_first_page_no_prev(self) -> None:
        """
        First page should have no previous URL.
        """

        request = make_request()
        result = PaginatedResult(
            items=[{'woe_id': WOE_ID_FIRST}, {'woe_id': WOE_ID_SECOND}],
            has_more=True,
        )
        pagination = PaginationParams(after=None, before=None, limit=DEFAULT_LIMIT, page=FIRST_PAGE)

        context = build_pagination_context(request, result, pagination=pagination, total=TOTAL_HUNDRED)

        assert context.urls.prev is None
        assert context.urls.next is not None
        assert f'after={WOE_ID_SECOND}' in context.urls.next

    def test_middle_page_has_both_urls(self) -> None:
        """
        Middle page should have both prev and next URLs.
        """

        request = make_request()
        result = PaginatedResult(
            items=[{'woe_id': WOE_ID_TEN}, {'woe_id': WOE_ID_TWENTY}],
            has_more=True,
        )
        pagination = PaginationParams(
            after=CURSOR_AFTER_FIVE,
            before=None,
            limit=DEFAULT_LIMIT,
            page=SECOND_PAGE,
        )

        context = build_pagination_context(request, result, pagination=pagination, total=TOTAL_HUNDRED)

        assert context.urls.prev is not None
        assert context.urls.next is not None
        assert f'before={WOE_ID_TEN}' in context.urls.prev
        assert f'after={WOE_ID_TWENTY}' in context.urls.next

    def test_last_page_no_next(self) -> None:
        """
        Last page should have no next URL.
        """

        request = make_request()
        result = PaginatedResult(
            items=[{'woe_id': WOE_ID_NINETY}, {'woe_id': WOE_ID_HUNDRED}],
            has_more=False,
        )
        pagination = PaginationParams(
            after=WOE_ID_EIGHTY,
            before=None,
            limit=DEFAULT_LIMIT,
            page=TENTH_PAGE,
        )

        context = build_pagination_context(request, result, pagination=pagination, total=TOTAL_HUNDRED)

        assert context.urls.prev is not None
        assert context.urls.next is None

    def test_pages_calculation(self) -> None:
        """
        Total pages should be calculated correctly.
        """

        request = make_request()
        result = PaginatedResult(items=[{'woe_id': WOE_ID_FIRST}], has_more=True)
        pagination = PaginationParams(after=None, before=None, limit=DEFAULT_LIMIT, page=FIRST_PAGE)

        context = build_pagination_context(request, result, pagination=pagination, total=TOTAL_NINETY_FIVE)

        assert context.pages == EXPECTED_PAGES_TEN


class TestBuildOffsetPaginationContext:
    """
    Tests for the build_offset_pagination_context function.
    """

    def test_empty_result_no_pagination(self) -> None:
        """
        Empty result should have no pagination URLs.
        """

        request = make_request()
        result = PaginatedResult(items=[], has_more=False)
        pagination = PaginationParams(after=None, before=None, limit=DEFAULT_LIMIT, page=FIRST_PAGE)

        context = build_offset_pagination_context(request, result, pagination=pagination, total=TOTAL_ZERO)

        assert context.urls.prev is None
        assert context.urls.next is None

    def test_first_page_no_prev(self) -> None:
        """
        First page should have no previous URL.
        """

        request = make_request()
        result = PaginatedResult(items=[{'woe_id': WOE_ID_FIRST}], has_more=True)
        pagination = PaginationParams(after=None, before=None, limit=DEFAULT_LIMIT, page=FIRST_PAGE)

        context = build_offset_pagination_context(request, result, pagination=pagination, total=TOTAL_FIFTY)

        assert context.urls.prev is None
        assert context.urls.next is not None
        assert f'page={SECOND_PAGE}' in context.urls.next

    def test_middle_page_has_both_urls(self) -> None:
        """
        Middle page should have both prev and next URLs.
        """

        request = make_request()
        result = PaginatedResult(items=[{'woe_id': WOE_ID_FIRST}], has_more=True)
        pagination = PaginationParams(after=None, before=None, limit=DEFAULT_LIMIT, page=THIRD_PAGE)

        context = build_offset_pagination_context(request, result, pagination=pagination, total=TOTAL_FIFTY)

        assert context.urls.prev is not None
        assert context.urls.next is not None
        assert f'page={SECOND_PAGE}' in context.urls.prev
        assert f'page={FOURTH_PAGE}' in context.urls.next

    def test_last_page_no_next(self) -> None:
        """
        Last page should have no next URL.
        """

        request = make_request()
        result = PaginatedResult(items=[{'woe_id': WOE_ID_FIRST}], has_more=False)
        pagination = PaginationParams(after=None, before=None, limit=DEFAULT_LIMIT, page=FIFTH_PAGE)

        context = build_offset_pagination_context(request, result, pagination=pagination, total=TOTAL_FIFTY)

        assert context.urls.prev is not None
        assert context.urls.next is None
