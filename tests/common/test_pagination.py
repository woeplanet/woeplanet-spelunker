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
        pagination = PaginationParams(after=None, before=None, limit=10, page=1)

        context = build_pagination_context(request, result, pagination=pagination, total=0)

        assert context.urls.prev is None
        assert context.urls.next is None
        assert context.page == 1
        assert context.pages == 1

    def test_first_page_no_prev(self) -> None:
        """
        First page should have no previous URL.
        """

        request = make_request()
        result = PaginatedResult(items=[{'woe_id': 1}, {'woe_id': 2}], has_more=True)
        pagination = PaginationParams(after=None, before=None, limit=10, page=1)

        context = build_pagination_context(request, result, pagination=pagination, total=100)

        assert context.urls.prev is None
        assert context.urls.next is not None
        assert 'after=2' in context.urls.next

    def test_middle_page_has_both_urls(self) -> None:
        """
        Middle page should have both prev and next URLs.
        """

        request = make_request()
        result = PaginatedResult(items=[{'woe_id': 10}, {'woe_id': 20}], has_more=True)
        pagination = PaginationParams(after=5, before=None, limit=10, page=2)

        context = build_pagination_context(request, result, pagination=pagination, total=100)

        assert context.urls.prev is not None
        assert context.urls.next is not None
        assert 'before=10' in context.urls.prev
        assert 'after=20' in context.urls.next

    def test_last_page_no_next(self) -> None:
        """
        Last page should have no next URL.
        """

        request = make_request()
        result = PaginatedResult(items=[{'woe_id': 90}, {'woe_id': 100}], has_more=False)
        pagination = PaginationParams(after=80, before=None, limit=10, page=10)

        context = build_pagination_context(request, result, pagination=pagination, total=100)

        assert context.urls.prev is not None
        assert context.urls.next is None

    def test_pages_calculation(self) -> None:
        """
        Total pages should be calculated correctly.
        """

        request = make_request()
        result = PaginatedResult(items=[{'woe_id': 1}], has_more=True)
        pagination = PaginationParams(after=None, before=None, limit=10, page=1)

        context = build_pagination_context(request, result, pagination=pagination, total=95)

        assert context.pages == 10


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
        pagination = PaginationParams(after=None, before=None, limit=10, page=1)

        context = build_offset_pagination_context(request, result, pagination=pagination, total=0)

        assert context.urls.prev is None
        assert context.urls.next is None

    def test_first_page_no_prev(self) -> None:
        """
        First page should have no previous URL.
        """

        request = make_request()
        result = PaginatedResult(items=[{'woe_id': 1}], has_more=True)
        pagination = PaginationParams(after=None, before=None, limit=10, page=1)

        context = build_offset_pagination_context(request, result, pagination=pagination, total=50)

        assert context.urls.prev is None
        assert context.urls.next is not None
        assert 'page=2' in context.urls.next

    def test_middle_page_has_both_urls(self) -> None:
        """
        Middle page should have both prev and next URLs.
        """

        request = make_request()
        result = PaginatedResult(items=[{'woe_id': 1}], has_more=True)
        pagination = PaginationParams(after=None, before=None, limit=10, page=3)

        context = build_offset_pagination_context(request, result, pagination=pagination, total=50)

        assert context.urls.prev is not None
        assert context.urls.next is not None
        assert 'page=2' in context.urls.prev
        assert 'page=4' in context.urls.next

    def test_last_page_no_next(self) -> None:
        """
        Last page should have no next URL.
        """

        request = make_request()
        result = PaginatedResult(items=[{'woe_id': 1}], has_more=False)
        pagination = PaginationParams(after=None, before=None, limit=10, page=5)

        context = build_offset_pagination_context(request, result, pagination=pagination, total=50)

        assert context.urls.prev is not None
        assert context.urls.next is None

