"""
WOEplanet Spelunker: tests package; endpoint tests.
"""

from http import HTTPStatus

from starlette.testclient import TestClient


class TestPlacetypesEndpoint:
    """
    Tests for the placetypes endpoints.
    """

    def test_placetypes_facets_returns_ok(self, client: TestClient) -> None:
        """
        Placetypes facets page should return 200 OK.
        """

        response = client.get('/placetypes')
        assert response.status_code == HTTPStatus.OK

    def test_placetype_search_returns_ok(self, client: TestClient) -> None:
        """
        Placetype search page should return 200 OK for valid placetype.
        """

        response = client.get('/placetypes/town')
        assert response.status_code == HTTPStatus.OK

    def test_placetype_search_not_found(self, client: TestClient) -> None:
        """
        Placetype search page should return 404 for invalid placetype.
        """

        response = client.get('/placetypes/nonexistent')
        assert response.status_code == HTTPStatus.NOT_FOUND
