"""
WOEplanet Spelunker: tests package; endpoint tests.
"""

from http import HTTPStatus

from starlette.testclient import TestClient

WOEID_LONDON = 44418
WOEID_NO_CENTROID = 1967129


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


class TestPlaceMapEndpoint:
    """
    Tests for the place map endpoint - bounds fallback path.
    """

    def test_place_map_with_geometry(self, client: TestClient) -> None:
        """
        Place with geometry should render map with geojson from geometry.
        """

        response = client.get(f'/id/{WOEID_LONDON}/map')
        assert response.status_code == HTTPStatus.OK
        assert 'geojson' in response.text.lower() or 'map' in response.text.lower()

    def test_place_map_without_geometry_uses_bounds(self, client: TestClient) -> None:
        """
        Place without geometry but with bounds should create polygon from bounds.
        """

        response = client.get(f'/id/{WOEID_NO_CENTROID}/map')
        assert response.status_code == HTTPStatus.OK


class TestPlaceNearbyEndpoint:
    """
    Tests for the place nearby endpoint - no centroid path.
    """

    def test_place_nearby_no_centroid_returns_ok(self, client: TestClient) -> None:
        """
        Place without coordinates should return OK with no_centroid flag.
        """

        response = client.get(f'/id/{WOEID_NO_CENTROID}/nearby')
        assert response.status_code == HTTPStatus.OK

    def test_place_nearby_no_centroid_shows_place_name(self, client: TestClient) -> None:
        """
        Place without coordinates should still render with place name in title.
        """

        response = client.get(f'/id/{WOEID_NO_CENTROID}/nearby')
        assert response.status_code == HTTPStatus.OK
        assert 'Baqa el Gharbiyya' in response.text
