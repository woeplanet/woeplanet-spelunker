"""
WOEplanet Spelunker: tests package; endpoint tests.
"""

from http import HTTPStatus

from starlette.testclient import TestClient


class TestCreditsEndpoint:
    """
    Tests for the credits endpoint.
    """

    def test_credits_returns_ok(self, client: TestClient) -> None:
        """
        Credits page should return 200 OK.
        """

        response = client.get('/credits')
        assert response.status_code == HTTPStatus.OK
