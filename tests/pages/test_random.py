"""
WOEplanet Spelunker: tests package; endpoint tests.
"""

from http import HTTPStatus

from starlette.testclient import TestClient


class TestRandomEndpoint:
    """
    Tests for the random endpoint.
    """

    def test_random_redirects(self, client: TestClient) -> None:
        """
        Random page should redirect to a place page.
        """

        response = client.get('/random', follow_redirects=False)
        assert response.status_code == HTTPStatus.TEMPORARY_REDIRECT
        assert '/id/' in response.headers['location']

    def test_random_returns_different_places(self, client: TestClient) -> None:
        """
        Multiple random requests should return different places (with high probability).
        """

        locations = set()
        for _ in range(5):
            response = client.get('/random', follow_redirects=False)
            locations.add(response.headers['location'])

        assert len(locations) > 1
