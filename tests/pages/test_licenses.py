"""
WOEplanet Spelunker: tests package; endpoint tests.
"""

from http import HTTPStatus

from starlette.testclient import TestClient


class TestLicensesEndpoint:
    """
    Tests for the licenses endpoint.
    """

    def test_licenses_returns_ok(self, client: TestClient) -> None:
        """
        Licenses page should return 200 OK.
        """

        response = client.get('/licenses')
        assert response.status_code == HTTPStatus.OK
