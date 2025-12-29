"""
WOEplanet Spelunker: tests package; endpoint tests.
"""

from http import HTTPStatus

from starlette.testclient import TestClient


class TestAboutEndpoint:
    """
    Tests for the about endpoint.
    """

    def test_about_returns_ok(self, client: TestClient) -> None:
        """
        About page should return 200 OK.
        """

        response = client.get('/about')
        assert response.status_code == HTTPStatus.OK
