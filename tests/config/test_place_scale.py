"""
WOEplanet Spelunker: tests package; place scale config tests.
"""

import pytest

from woeplanet.spelunker.config.place_scale import PLACETYPE_TO_SCALE, placetype_to_scale

PLACETYPE_ID_COUNTRY = 12
PLACETYPE_ID_TOWN = 7
PLACETYPE_ID_CONTINENT = 29
PLACETYPE_ID_UNKNOWN = 999

SCALE_COUNTRY = 5
SCALE_TOWN = 16
SCALE_CONTINENT = 2
SCALE_UNKNOWN = 0


class TestPlacetypeToScale:
    """
    Tests for the placetype_to_scale function.
    """

    def test_unknown_placetype_returns_zero(self) -> None:
        """
        Unknown placetype ID should return 0.
        """

        assert placetype_to_scale(PLACETYPE_ID_UNKNOWN) == SCALE_UNKNOWN

    def test_country_scale(self) -> None:
        """
        Country placetype should return scale 5.
        """

        assert placetype_to_scale(PLACETYPE_ID_COUNTRY) == SCALE_COUNTRY

    def test_town_scale(self) -> None:
        """
        Town placetype should return scale 16.
        """

        assert placetype_to_scale(PLACETYPE_ID_TOWN) == SCALE_TOWN

    def test_continent_scale(self) -> None:
        """
        Continent placetype should return scale 2.
        """

        assert placetype_to_scale(PLACETYPE_ID_CONTINENT) == SCALE_CONTINENT

    @pytest.mark.parametrize(
        ('placetype_id', 'expected_scale'),
        [
            (19, 1),  # supername
            (29, 2),  # continent
            (38, 3),  # sea
            (12, 5),  # country
            (8, 6),  # state
            (9, 9),  # county
            (7, 16),  # town
            (22, 17),  # suburb
            (20, 19),  # poi
            (6, 21),  # street
            (11, 22),  # zip
        ],
    )
    def test_known_placetypes(self, placetype_id: int, expected_scale: int) -> None:
        """
        Known placetype IDs should return correct scales.
        """

        assert placetype_to_scale(placetype_id) == expected_scale

    def test_all_mappings_defined(self) -> None:
        """
        All defined mappings should be tested.
        """

        for placetype_id, expected_scale in PLACETYPE_TO_SCALE.items():
            assert placetype_to_scale(placetype_id) == expected_scale
