"""
WOEplanet Spelunker: tests package; endpoint tests.
"""

from http import HTTPStatus

from starlette.testclient import TestClient


class TestSearchEndpoint:
    """
    Tests for the search endpoint.
    """

    def test_search_form_returns_ok(self, client: TestClient) -> None:
        """
        Search page without query should return 200 OK (shows form).
        """

        response = client.get('/search')
        assert response.status_code == HTTPStatus.OK

    def test_search_name_returns_ok(self, client: TestClient) -> None:
        """
        Search page with name query should return 200 OK.
        """

        response = client.get('/search?q=London')
        assert response.status_code == HTTPStatus.OK

    def test_search_woeid_redirects(self, client: TestClient) -> None:
        """
        Search with WOEID type should redirect to place page.
        """

        response = client.get('/search?q=44418&name-type=woeid', follow_redirects=False)
        assert response.status_code == HTTPStatus.FOUND
        assert response.headers['location'] == '/id/44418'

    def test_search_invalid_woeid(self, client: TestClient) -> None:
        """
        Search with invalid WOEID should return 400.
        """

        response = client.get('/search?q=notanumber&name-type=woeid')
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_search_with_name_type_filter(self, client: TestClient) -> None:
        """
        Search with name_type filter should return 200 OK.
        """

        response = client.get('/search?q=London&name-type=P')
        assert response.status_code == HTTPStatus.OK
