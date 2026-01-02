"""
WOEplanet Spelunker: tests package; endpoint tests.
"""

from http import HTTPStatus

from starlette.testclient import TestClient


class TestStaticFiles:
    """
    Tests for static file serving.
    """

    def test_static_css_returns_ok(self, client: TestClient) -> None:
        """
        Static CSS file should return 200 OK.
        """

        response = client.get('/static/css/woeplanet.css')
        assert response.status_code == HTTPStatus.OK

    def test_static_not_found(self, client: TestClient) -> None:
        """
        Non-existent static file should return 404.
        """

        response = client.get('/static/nonexistent.css')
        assert response.status_code == HTTPStatus.NOT_FOUND
