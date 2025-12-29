"""
WOEplanet Spelunker: tests package; endpoint tests.
"""

from http import HTTPStatus

from starlette.testclient import TestClient


class TestPagination:
    """
    Tests for pagination query parameters.
    """

    def test_pagination_limit(self, client: TestClient) -> None:
        """
        Pagination with limit should return 200 OK.
        """

        response = client.get('/countries/GB?limit=5')
        assert response.status_code == HTTPStatus.OK

    def test_pagination_page(self, client: TestClient) -> None:
        """
        Pagination with page should return 200 OK.
        """

        response = client.get('/placetypes/town?page=2')
        assert response.status_code == HTTPStatus.OK

    def test_pagination_after(self, client: TestClient) -> None:
        """
        Pagination with after cursor should return 200 OK.
        """

        response = client.get('/placetypes/town?after=1000')
        assert response.status_code == HTTPStatus.OK
