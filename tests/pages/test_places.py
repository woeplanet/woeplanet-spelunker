"""
WOEplanet Spelunker: tests package; endpoint tests.
"""

from http import HTTPStatus

from starlette.testclient import TestClient


class TestPlaceEndpoint:
    """
    Tests for the place endpoints.
    """

    def test_place_returns_ok(self, client: TestClient) -> None:
        """
        Place page should return 200 OK for valid WOEID.
        """

        response = client.get('/id/44418')
        assert response.status_code == HTTPStatus.OK

    def test_place_not_found(self, client: TestClient) -> None:
        """
        Place page should return 404 for non-existent WOEID.
        """

        response = client.get('/id/999999999')
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_place_negative_woeid_not_matched(self, client: TestClient) -> None:
        """
        Negative WOEID doesn't match route pattern, returns 404.
        """

        response = client.get('/id/-1')
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_place_map_returns_ok(self, client: TestClient) -> None:
        """
        Place map page should return 200 OK for valid WOEID.
        """

        response = client.get('/id/44418/map')
        assert response.status_code == HTTPStatus.OK

    def test_place_nearby_returns_ok(self, client: TestClient) -> None:
        """
        Place nearby page should return 200 OK for valid WOEID.
        """

        response = client.get('/id/44418/nearby')
        assert response.status_code == HTTPStatus.OK
