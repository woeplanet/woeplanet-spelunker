"""
WOEplanet Spelunker: tests package; endpoint tests.
"""

from http import HTTPStatus

from starlette.testclient import TestClient


class TestNearbyEndpoint:
    """
    Tests for the nearby endpoint.
    """

    def test_nearby_no_coords_returns_ok(self, client: TestClient) -> None:
        """
        Nearby page without coords should return 200 OK (shows form).
        """

        response = client.get('/nearby')
        assert response.status_code == HTTPStatus.OK

    def test_nearby_with_coords_returns_ok(self, client: TestClient) -> None:
        """
        Nearby page with coords should return 200 OK.
        """

        response = client.get('/nearby?lat=51.5074&lng=-0.1278')
        assert response.status_code == HTTPStatus.OK

    def test_nearby_with_distance_returns_ok(self, client: TestClient) -> None:
        """
        Nearby page with custom distance should return 200 OK.
        """

        response = client.get('/nearby?lat=51.5074&lng=-0.1278&distance=10000')
        assert response.status_code == HTTPStatus.OK
