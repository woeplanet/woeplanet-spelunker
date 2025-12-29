"""
WOEplanet Spelunker: tests package; endpoint tests.
"""

from http import HTTPStatus

from starlette.testclient import TestClient


class TestIndexEndpoint:
    """
    Tests for the index endpoint.
    """

    def test_index_returns_ok(self, client: TestClient) -> None:
        """
        Index page should return 200 OK.
        """

        response = client.get('/')
        assert response.status_code == HTTPStatus.OK

    def test_index_returns_html(self, client: TestClient) -> None:
        """
        Index page should return HTML content.
        """

        response = client.get('/')
        assert 'text/html' in response.headers['content-type']
