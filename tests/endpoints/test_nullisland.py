"""
WOEplanet Spelunker: tests package; endpoint tests.
"""

from http import HTTPStatus

from starlette.testclient import TestClient


class TestNullIslandEndpoint:
    """
    Tests for the null island endpoint.
    """

    def test_nullisland_returns_ok(self, client: TestClient) -> None:
        """
        Null Island page should return 200 OK.
        """

        response = client.get('/nullisland')
        assert response.status_code == HTTPStatus.OK
