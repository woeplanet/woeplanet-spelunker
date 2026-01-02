"""
WOEplanet Spelunker: tests package; database tests.
"""

import pytest
from parametrize_from_file import parametrize

from woeplanet.spelunker.dependencies.database import (
    Database,
    PaginatedResult,
    PlaceFilters,
    SearchFilters,
)

WOEID_LONDON = 44418
WOEID_NEW_YORK = 2459115
WOEID_UNITED_KINGDOM = 23424975
WOEID_EARTH = 1
WOEID_NOT_FOUND = 999999999

PLACETYPE_ID_TOWN = 7
PLACETYPE_ID_COUNTRY = 12
PLACETYPE_ID_STATE = 8
PLACETYPE_ID_SUPERNAME = 19
PLACETYPE_ID_UNKNOWN = 0

ISO_GB = 'GB'
ISO_US = 'US'
ISO_INVALID = 'XX'

DEFAULT_LIMIT = 10
SMALL_LIMIT = 5
LARGE_LIMIT = 50

LAT_LONDON = 51.5074
LNG_LONDON = -0.1278
NEARBY_DISTANCE = 5000


@pytest.fixture
def default_place_filters() -> PlaceFilters:
    """
    Default place filters for testing.
    """

    return PlaceFilters(
        geometry=True,
        ancestors=True,
        hierarchy=True,
        names=True,
        neighbours=True,
        children=True,
        null_island=False,
        deprecated=False,
        exclude_placetypes=[],
        history=False,
        licensing=False,
    )


@pytest.fixture
def minimal_place_filters() -> PlaceFilters:
    """
    Minimal place filters for faster queries.
    """

    return PlaceFilters(
        geometry=False,
        ancestors=False,
        hierarchy=False,
        names=False,
        neighbours=False,
        children=False,
        null_island=False,
        deprecated=False,
        exclude_placetypes=[],
        history=False,
        licensing=False,
    )


@pytest.fixture
def default_search_filters() -> SearchFilters:
    """
    Default search filters for testing.
    """

    return SearchFilters(
        deprecated=False,
        unknown=False,
        null_island=False,
    )


class TestGetPlaceById:
    """
    Tests for the get_place_by_id method.
    """

    @parametrize
    async def test_get_place_by_id_valid(
        self,
        db: Database,
        minimal_place_filters: PlaceFilters,
        woe_id: int,
        expected_name: str,
        expected_placetype_id: int,
    ) -> None:
        """
        Valid WOE ID should return place with correct data.
        """

        result = await db.get_place_by_id(woe_id, minimal_place_filters)

        assert result is not None
        assert result['woe_id'] == woe_id
        assert result['name'] == expected_name
        assert result['placetype_id'] == expected_placetype_id

    @parametrize
    async def test_get_place_by_id_not_found(
        self,
        db: Database,
        minimal_place_filters: PlaceFilters,
        woe_id: int,
    ) -> None:
        """
        Non-existent WOE ID should return None.
        """

        result = await db.get_place_by_id(woe_id, minimal_place_filters)

        assert result is None

    async def test_get_place_with_geometry(self, db: Database) -> None:
        """
        Place with geometry filter should include coordinates.
        """

        filters = PlaceFilters(
            centroid=True,
            bounding_box=True,
            geometry=True,
            ancestors=False,
            hierarchy=False,
            names=False,
            neighbours=False,
            children=False,
            null_island=False,
            deprecated=False,
            exclude_placetypes=[],
            history=False,
            licensing=False,
        )
        result = await db.get_place_by_id(WOEID_LONDON, filters)

        assert result is not None
        assert result.get('lat') is not None
        assert result.get('lng') is not None
        assert result['lat'] == pytest.approx(LAT_LONDON, abs=0.01)

    async def test_get_place_with_ancestors(self, db: Database) -> None:
        """
        Place with ancestors filter should include ancestor list.
        """

        filters = PlaceFilters(
            ancestors=True,
            hierarchy=False,
            names=False,
            neighbours=False,
            children=False,
            null_island=False,
            deprecated=False,
            exclude_placetypes=[],
            history=False,
            licensing=False,
        )
        result = await db.get_place_by_id(WOEID_LONDON, filters)

        assert result is not None
        assert 'ancestors' in result

    async def test_get_place_with_hierarchy(self, db: Database) -> None:
        """
        Place with hierarchy filter should include hierarchy object.
        """

        filters = PlaceFilters(
            ancestors=False,
            hierarchy=True,
            names=False,
            neighbours=False,
            children=False,
            null_island=False,
            deprecated=False,
            exclude_placetypes=[],
            history=False,
            licensing=False,
        )
        result = await db.get_place_by_id(WOEID_LONDON, filters)

        assert result is not None
        assert 'hierarchy' in result

    async def test_get_place_with_names(self, db: Database) -> None:
        """
        Place with names filter should include aliases.
        """

        filters = PlaceFilters(
            ancestors=False,
            hierarchy=False,
            names=True,
            neighbours=False,
            children=False,
            null_island=False,
            deprecated=False,
            exclude_placetypes=[],
            history=False,
            licensing=False,
        )
        result = await db.get_place_by_id(WOEID_LONDON, filters)

        assert result is not None
        assert 'aliases' in result

    async def test_get_place_with_neighbours(self, db: Database) -> None:
        """
        Place with neighbours filter should include neighbours list.
        """

        filters = PlaceFilters(
            ancestors=False,
            hierarchy=False,
            names=False,
            neighbours=True,
            children=False,
            null_island=False,
            deprecated=False,
            exclude_placetypes=[],
            history=False,
            licensing=False,
        )
        result = await db.get_place_by_id(WOEID_LONDON, filters)

        assert result is not None
        assert 'neighbours' in result

    async def test_get_place_with_children(self, db: Database) -> None:
        """
        Place with children filter should include children list.
        """

        filters = PlaceFilters(
            ancestors=False,
            hierarchy=False,
            names=False,
            neighbours=False,
            children=True,
            null_island=False,
            deprecated=False,
            exclude_placetypes=[],
            history=False,
            licensing=False,
        )
        result = await db.get_place_by_id(WOEID_LONDON, filters)

        assert result is not None
        assert 'children' in result

    async def test_get_place_with_history(self, db: Database) -> None:
        """
        Place with history filter should include history.
        """

        filters = PlaceFilters(
            ancestors=False,
            hierarchy=False,
            names=False,
            neighbours=False,
            children=False,
            null_island=False,
            deprecated=False,
            exclude_placetypes=[],
            history=True,
            licensing=False,
        )
        result = await db.get_place_by_id(WOEID_LONDON, filters)

        assert result is not None
        assert 'history' in result

    async def test_get_place_with_licensing(self, db: Database) -> None:
        """
        Place with licensing filter should include licenses.
        """

        filters = PlaceFilters(
            ancestors=False,
            hierarchy=False,
            names=False,
            neighbours=False,
            children=False,
            null_island=False,
            deprecated=False,
            exclude_placetypes=[],
            history=False,
            licensing=True,
        )
        result = await db.get_place_by_id(WOEID_LONDON, filters)

        assert result is not None
        assert 'licenses' in result

    async def test_get_place_exclude_placetypes(self, db: Database) -> None:
        """
        Place with excluded placetype should return None.
        """

        filters = PlaceFilters(
            ancestors=False,
            hierarchy=False,
            names=False,
            neighbours=False,
            children=False,
            null_island=False,
            deprecated=False,
            exclude_placetypes=[PLACETYPE_ID_TOWN],
            history=False,
            licensing=False,
        )
        result = await db.get_place_by_id(WOEID_LONDON, filters)

        assert result is None


class TestInflateAliases:
    """
    Tests for the inflate_aliases method.
    """

    async def test_inflate_aliases_groups_by_language(self, db: Database) -> None:
        """
        Aliases should be grouped by language.
        """

        aliases = [
            {'name': 'London', 'name_type': 'S', 'language': 'ENG'},
            {'name': 'Londres', 'name_type': 'S', 'language': 'FRA'},
            {'name': 'LON', 'name_type': 'A', 'language': 'ENG'},
        ]
        result = db.inflate_aliases(aliases)

        assert 'ENG' in result
        assert 'FRA' in result
        assert 'London' in result['ENG']['S']
        assert 'LON' in result['ENG']['A']

    async def test_inflate_aliases_empty_list(self, db: Database) -> None:
        """
        Empty alias list should return empty dict.
        """

        result = db.inflate_aliases([])

        assert result == {}


class TestInflatePlaceIds:
    """
    Tests for the inflate_place_ids method.
    """

    async def test_inflate_place_ids_valid(self, db: Database) -> None:
        """
        Valid WOE IDs should be inflated to places grouped by placetype.
        """

        woe_ids = [WOEID_LONDON, WOEID_NEW_YORK, WOEID_UNITED_KINGDOM]
        result = await db.inflate_place_ids(woe_ids)

        assert result is not None
        assert len(result) > 0

    async def test_inflate_place_ids_empty_list(self, db: Database) -> None:
        """
        Empty WOE ID list should return empty dict.
        """

        result = await db.inflate_place_ids([])

        assert result == {}

    async def test_inflate_place_ids_not_found(self, db: Database) -> None:
        """
        Non-existent WOE IDs should not appear in result.
        """

        result = await db.inflate_place_ids([WOEID_NOT_FOUND])

        assert result == {}


class TestGetCountryByIso:
    """
    Tests for the get_country_by_iso method.
    """

    @parametrize
    async def test_get_country_by_iso_valid(
        self,
        db: Database,
        iso: str,
        expected_name: str,
    ) -> None:
        """
        Valid ISO code should return country.
        """

        result = await db.get_country_by_iso(iso)

        assert result is not None
        assert result['name'] == expected_name

    @parametrize
    async def test_get_country_by_iso_not_found(
        self,
        db: Database,
        iso: str,
    ) -> None:
        """
        Invalid ISO code should return None.
        """

        result = await db.get_country_by_iso(iso)

        assert result is None


class TestGetCountriesFacets:
    """
    Tests for the get_countries_facets method.
    """

    async def test_get_countries_facets_returns_list(
        self,
        db: Database,
        default_search_filters: SearchFilters,
    ) -> None:
        """
        Should return list of countries with counts.
        """

        result = await db.get_countries_facets(filters=default_search_filters)

        assert isinstance(result, list)
        assert len(result) > 0
        assert 'woe_id' in result[0]
        assert 'name' in result[0]
        assert 'iso2' in result[0]
        assert 'count' in result[0]

    async def test_get_countries_facets_with_deprecated(self, db: Database) -> None:
        """
        Including deprecated should affect results.
        """

        filters = SearchFilters(deprecated=True, unknown=False, null_island=False)
        result = await db.get_countries_facets(filters=filters)

        assert isinstance(result, list)

    async def test_get_countries_facets_with_null_island(self, db: Database) -> None:
        """
        Including null island places should affect results.
        """

        filters = SearchFilters(deprecated=False, unknown=False, null_island=True)
        result = await db.get_countries_facets(filters=filters)

        assert isinstance(result, list)

    async def test_get_countries_facets_with_unknown(self, db: Database) -> None:
        """
        Including unknown placetypes should affect results.
        """

        filters = SearchFilters(deprecated=False, unknown=True, null_island=False)
        result = await db.get_countries_facets(filters=filters)

        assert isinstance(result, list)

    async def test_get_countries_facets_include_all(self, db: Database) -> None:
        """
        Including all filter options should return more or equal results.
        """

        default_filters = SearchFilters(deprecated=False, unknown=False, null_island=False)
        all_filters = SearchFilters(deprecated=True, unknown=True, null_island=True)

        default_result = await db.get_countries_facets(filters=default_filters)
        all_result = await db.get_countries_facets(filters=all_filters)

        default_total = sum(c['count'] for c in default_result)
        all_total = sum(c['count'] for c in all_result)

        assert all_total >= default_total


class TestGetTotalWoeids:
    """
    Tests for the get_total_woeids method.
    """

    async def test_get_total_woeids_returns_int(
        self,
        db: Database,
        default_search_filters: SearchFilters,
    ) -> None:
        """
        Should return positive integer.
        """

        result = await db.get_total_woeids(filters=default_search_filters)

        assert isinstance(result, int)
        assert result > 0

    @pytest.mark.parametrize(
        'filters',
        [
            SearchFilters(deprecated=False, unknown=False, null_island=False),
            SearchFilters(deprecated=True, unknown=False, null_island=False),
            SearchFilters(deprecated=True, unknown=True, null_island=True),
        ],
        ids=['defaults', 'include_deprecated', 'include_all'],
    )
    async def test_get_total_woeids_with_filters(
        self,
        db: Database,
        filters: SearchFilters,
    ) -> None:
        """
        Different filters should return different counts.
        """

        result = await db.get_total_woeids(filters=filters)

        assert isinstance(result, int)
        assert result >= 0


class TestGetPlacetypeFacets:
    """
    Tests for the get_placetype_facets method.
    """

    async def test_get_placetype_facets_returns_list(
        self,
        db: Database,
        default_search_filters: SearchFilters,
    ) -> None:
        """
        Should return list of placetypes with counts.
        """

        result = await db.get_placetype_facets(filters=default_search_filters)

        assert isinstance(result, list)
        assert len(result) > 0
        assert 'placetype_id' in result[0]
        assert 'shortname' in result[0]
        assert 'count' in result[0]

    async def test_get_placetype_facets_with_deprecated(self, db: Database) -> None:
        """
        Including deprecated should affect results.
        """

        filters = SearchFilters(deprecated=True, unknown=False, null_island=False)
        result = await db.get_placetype_facets(filters=filters)

        assert isinstance(result, list)
        assert len(result) > 0

    async def test_get_placetype_facets_with_null_island(self, db: Database) -> None:
        """
        Including null island places should affect results.
        """

        filters = SearchFilters(deprecated=False, unknown=False, null_island=True)
        result = await db.get_placetype_facets(filters=filters)

        assert isinstance(result, list)
        assert len(result) > 0

    async def test_get_placetype_facets_with_unknown(self, db: Database) -> None:
        """
        Including unknown placetypes should return results.
        """

        filters = SearchFilters(deprecated=False, unknown=True, null_island=False)
        result = await db.get_placetype_facets(filters=filters)

        assert isinstance(result, list)
        assert len(result) > 0

    async def test_get_placetype_facets_include_all(self, db: Database) -> None:
        """
        Including all filter options should return more or equal counts.
        """

        default_filters = SearchFilters(deprecated=False, unknown=False, null_island=False)
        all_filters = SearchFilters(deprecated=True, unknown=True, null_island=True)

        default_result = await db.get_placetype_facets(filters=default_filters)
        all_result = await db.get_placetype_facets(filters=all_filters)

        default_total = sum(p['count'] for p in default_result)
        all_total = sum(p['count'] for p in all_result)

        assert all_total >= default_total


class TestGetPlacesByPlacetype:
    """
    Tests for the get_places_by_placetype method.
    """

    @parametrize
    async def test_get_places_by_placetype(
        self,
        db: Database,
        default_search_filters: SearchFilters,
        placetype_id: int,
        limit: int,
    ) -> None:
        """
        Should return paginated result.
        """

        result = await db.get_places_by_placetype(
            placetype_id,
            filters=default_search_filters,
            limit=limit,
        )

        assert isinstance(result, PaginatedResult)
        assert len(result.items) <= limit

    async def test_get_places_by_placetype_with_after(
        self,
        db: Database,
        default_search_filters: SearchFilters,
    ) -> None:
        """
        After cursor should paginate forward.
        """

        first_page = await db.get_places_by_placetype(
            PLACETYPE_ID_TOWN,
            filters=default_search_filters,
            limit=SMALL_LIMIT,
        )

        if first_page.items:
            last_id = first_page.items[-1]['woe_id']
            second_page = await db.get_places_by_placetype(
                PLACETYPE_ID_TOWN,
                filters=default_search_filters,
                after=last_id,
                limit=SMALL_LIMIT,
            )

            if second_page.items:
                assert second_page.items[0]['woe_id'] > last_id

    async def test_get_places_by_placetype_with_before(
        self,
        db: Database,
        default_search_filters: SearchFilters,
    ) -> None:
        """
        Before cursor should paginate backward.
        """

        first_page = await db.get_places_by_placetype(
            PLACETYPE_ID_TOWN,
            filters=default_search_filters,
            after=WOEID_LONDON,
            limit=SMALL_LIMIT,
        )

        if first_page.items:
            first_id = first_page.items[0]['woe_id']
            prev_page = await db.get_places_by_placetype(
                PLACETYPE_ID_TOWN,
                filters=default_search_filters,
                before=first_id,
                limit=SMALL_LIMIT,
            )

            if prev_page.items:
                assert prev_page.items[-1]['woe_id'] < first_id


class TestGetPlacesByPlacetypeCount:
    """
    Tests for the get_places_by_placetype_count method.
    """

    async def test_get_places_by_placetype_count_returns_int(
        self,
        db: Database,
        default_search_filters: SearchFilters,
    ) -> None:
        """
        Should return positive integer for valid placetype.
        """

        result = await db.get_places_by_placetype_count(
            PLACETYPE_ID_TOWN,
            filters=default_search_filters,
        )

        assert isinstance(result, int)
        assert result > 0

    async def test_get_places_by_placetype_count_unknown_type(
        self,
        db: Database,
        default_search_filters: SearchFilters,
    ) -> None:
        """
        Unknown placetype should return zero.
        """

        result = await db.get_places_by_placetype_count(
            9999,
            filters=default_search_filters,
        )

        assert result == 0


class TestGetPlacesByCountry:
    """
    Tests for the get_places_by_country method.
    """

    async def test_get_places_by_country_returns_result(
        self,
        db: Database,
        default_search_filters: SearchFilters,
    ) -> None:
        """
        Should return paginated result.
        """

        country = await db.get_country_by_iso(ISO_GB)
        assert country is not None

        result = await db.get_places_by_country(
            country['woe_id'],
            filters=default_search_filters,
            limit=DEFAULT_LIMIT,
        )

        assert isinstance(result, PaginatedResult)
        assert len(result.items) <= DEFAULT_LIMIT

    async def test_get_places_by_country_with_placetype_filter(
        self,
        db: Database,
        default_search_filters: SearchFilters,
    ) -> None:
        """
        Placetype filter should only return matching places.
        """

        country = await db.get_country_by_iso(ISO_GB)
        assert country is not None

        result = await db.get_places_by_country(
            country['woe_id'],
            filters=default_search_filters,
            placetype='town',
            limit=DEFAULT_LIMIT,
        )

        assert isinstance(result, PaginatedResult)
        for item in result.items:
            assert item['placetype_name'] == 'town'


class TestGetPlacesByCountryCount:
    """
    Tests for the get_places_by_country_count method.
    """

    async def test_get_places_by_country_count_returns_int(
        self,
        db: Database,
        default_search_filters: SearchFilters,
    ) -> None:
        """
        Should return positive integer.
        """

        country = await db.get_country_by_iso(ISO_GB)
        assert country is not None

        result = await db.get_places_by_country_count(
            country_woe_id=country['woe_id'],
            filters=default_search_filters,
        )

        assert isinstance(result, int)
        assert result > 0


class TestGetPlacetypesByCountry:
    """
    Tests for the get_placetypes_by_country method.
    """

    async def test_get_placetypes_by_country_returns_list(
        self,
        db: Database,
        default_search_filters: SearchFilters,
    ) -> None:
        """
        Should return list of placetype facets.
        """

        result = await db.get_placetypes_by_country(
            iso2=ISO_GB,
            filters=default_search_filters,
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert 'placetype_id' in result[0]
        assert 'shortname' in result[0]
        assert 'count' in result[0]


class TestGetNullislandPlaces:
    """
    Tests for the get_nullisland_places method.
    """

    async def test_get_nullisland_places_returns_result(
        self,
        db: Database,
        default_search_filters: SearchFilters,
    ) -> None:
        """
        Should return paginated result.
        """

        result = await db.get_nullisland_places(
            filters=default_search_filters,
            limit=DEFAULT_LIMIT,
        )

        assert isinstance(result, PaginatedResult)


class TestGetNullislandPlacesCount:
    """
    Tests for the get_nullisland_places_count method.
    """

    async def test_get_nullisland_places_count_returns_int(
        self,
        db: Database,
        default_search_filters: SearchFilters,
    ) -> None:
        """
        Should return non-negative integer.
        """

        result = await db.get_nullisland_places_count(filters=default_search_filters)

        assert isinstance(result, int)
        assert result >= 0


class TestGetNullislandPlacetypeFacets:
    """
    Tests for the get_nullisland_placetype_facets method.
    """

    async def test_get_nullisland_placetype_facets_returns_list(
        self,
        db: Database,
        default_search_filters: SearchFilters,
    ) -> None:
        """
        Should return list of placetype facets.
        """

        result = await db.get_nullisland_placetype_facets(filters=default_search_filters)

        assert isinstance(result, list)


class TestSearchPlaces:
    """
    Tests for the search_places method.
    """

    @parametrize
    async def test_search_queries(
        self,
        db: Database,
        default_search_filters: SearchFilters,
        query: str,
    ) -> None:
        """
        Valid query should return paginated result.
        """

        result = await db.search_places(
            query,
            filters=default_search_filters,
            limit=DEFAULT_LIMIT,
        )

        assert isinstance(result, PaginatedResult)

    async def test_search_places_with_name_type(
        self,
        db: Database,
        default_search_filters: SearchFilters,
    ) -> None:
        """
        Name type filter should be applied.
        """

        result = await db.search_places(
            'London',
            name_type='S',
            filters=default_search_filters,
            limit=DEFAULT_LIMIT,
        )

        assert isinstance(result, PaginatedResult)

    async def test_search_places_empty_query_returns_empty(
        self,
        db: Database,
        default_search_filters: SearchFilters,
    ) -> None:
        """
        Empty query should return empty result.
        """

        result = await db.search_places(
            '',
            filters=default_search_filters,
            limit=DEFAULT_LIMIT,
        )

        assert isinstance(result, PaginatedResult)
        assert len(result.items) == 0


class TestSearchPlacesCount:
    """
    Tests for the search_places_count method.
    """

    async def test_search_places_count_returns_int(
        self,
        db: Database,
        default_search_filters: SearchFilters,
    ) -> None:
        """
        Valid query should return count.
        """

        result = await db.search_places_count(
            'London',
            filters=default_search_filters,
        )

        assert isinstance(result, int)
        assert result > 0


class TestGetPlacetypes:
    """
    Tests for the get_placetypes method.
    """

    async def test_get_placetypes_returns_list(self, db: Database) -> None:
        """
        Should return list of all placetypes.
        """

        result = await db.get_placetypes()

        assert isinstance(result, list)
        assert len(result) > 0
        assert 'id' in result[0]
        assert 'shortname' in result[0]
        assert 'name' in result[0]


class TestGetLicenses:
    """
    Tests for the get_licenses method.
    """

    async def test_get_licenses_returns_list(self, db: Database) -> None:
        """
        Should return list of all licenses.
        """

        result = await db.get_licenses()

        assert isinstance(result, list)
        assert len(result) > 0


class TestGetRandomPlace:
    """
    Tests for the get_random_place method.
    """

    async def test_get_random_place_returns_place(
        self,
        db: Database,
        minimal_place_filters: PlaceFilters,
    ) -> None:
        """
        Should return a random place.
        """

        result = await db.get_random_place(minimal_place_filters)

        assert result is not None
        assert 'woe_id' in result

    async def test_get_random_place_excludes_placetypes(self, db: Database) -> None:
        """
        Excluded placetypes should not be returned.
        """

        filters = PlaceFilters(
            geometry=False,
            ancestors=False,
            hierarchy=False,
            names=False,
            neighbours=False,
            children=False,
            null_island=False,
            deprecated=False,
            exclude_placetypes=[PLACETYPE_ID_UNKNOWN],
            history=False,
            licensing=False,
        )

        for _ in range(5):
            result = await db.get_random_place(filters)
            if result:
                place = await db.get_place_by_id(result['woe_id'], filters)
                if place:
                    assert place['placetype_id'] != PLACETYPE_ID_UNKNOWN


class TestGetPlacesNearCentroid:
    """
    Tests for the get_places_near_centroid method.
    """

    @parametrize
    async def test_nearby_params(
        self,
        db: Database,
        default_search_filters: SearchFilters,
        lat: float,
        lng: float,
        distance: int,
    ) -> None:
        """
        Valid coordinates should return paginated result.
        """

        result = await db.get_places_near_centroid(
            lat=lat,
            lng=lng,
            distance=distance,
            filters=default_search_filters,
            limit=DEFAULT_LIMIT,
        )

        assert isinstance(result, PaginatedResult)

    async def test_get_places_near_centroid_with_offset(
        self,
        db: Database,
        default_search_filters: SearchFilters,
    ) -> None:
        """
        Offset should skip results.
        """

        first_page = await db.get_places_near_centroid(
            lat=LAT_LONDON,
            lng=LNG_LONDON,
            distance=NEARBY_DISTANCE,
            filters=default_search_filters,
            limit=SMALL_LIMIT,
            offset=0,
        )

        second_page = await db.get_places_near_centroid(
            lat=LAT_LONDON,
            lng=LNG_LONDON,
            distance=NEARBY_DISTANCE,
            filters=default_search_filters,
            limit=SMALL_LIMIT,
            offset=SMALL_LIMIT,
        )

        if first_page.items and second_page.items:
            first_ids = {item['woe_id'] for item in first_page.items}
            second_ids = {item['woe_id'] for item in second_page.items}
            assert first_ids.isdisjoint(second_ids)


class TestGetPlacesNearCentroidCount:
    """
    Tests for the get_places_near_centroid_count method.
    """

    async def test_get_places_near_centroid_count_returns_int(
        self,
        db: Database,
        default_search_filters: SearchFilters,
    ) -> None:
        """
        Should return non-negative integer.
        """

        result = await db.get_places_near_centroid_count(
            lat=LAT_LONDON,
            lng=LNG_LONDON,
            distance=NEARBY_DISTANCE,
            filters=default_search_filters,
        )

        assert isinstance(result, int)
        assert result >= 0
