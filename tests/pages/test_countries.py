"""
WOEplanet Spelunker: tests package; endpoint tests.
"""

from http import HTTPStatus

from starlette.testclient import TestClient


class TestCountriesEndpoint:
    """
    Tests for the countries endpoints.
    """

    def test_countries_facets_returns_ok(self, client: TestClient) -> None:
        """
        Countries facets page should return 200 OK.
        """

        response = client.get('/countries')
        assert response.status_code == HTTPStatus.OK

    def test_country_search_returns_ok(self, client: TestClient) -> None:
        """
        Country search page should return 200 OK for valid ISO code.
        """

        response = client.get('/countries/GB')
        assert response.status_code == HTTPStatus.OK

    def test_country_search_not_found(self, client: TestClient) -> None:
        """
        Country search page should return 404 for invalid ISO code.
        """

        response = client.get('/countries/XX')
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_country_search_with_include_filters(self, client: TestClient) -> None:
        """
        Country search page should accept include filters.
        """

        response = client.get('/countries/GB?include=deprecated')
        assert response.status_code == HTTPStatus.OK
