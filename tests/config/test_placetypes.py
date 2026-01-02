"""
WOEplanet Spelunker: tests package; placetypes config tests.
"""

import pytest

from woeplanet.spelunker.config.placetypes import (
    PLACETYPE_BY_ID,
    PLACETYPE_COUNTRY,
    PLACETYPE_ID,
    PLACETYPE_UNKNOWN,
    Placetype,
    placetype_id_to_shortname,
    placetype_shortname_to_id,
)

EXPECTED_COUNTRY_ID = 12
EXPECTED_TOWN_ID = 7
EXPECTED_UNKNOWN_ID = 0


class TestPlacetypeEnum:
    """
    Tests for the Placetype enum.
    """

    def test_placetype_is_str_enum(self) -> None:
        """
        Placetype enum values should be strings.
        """

        assert isinstance(Placetype.TOWN, str)
        assert Placetype.TOWN == 'town'

    def test_all_placetypes_are_lowercase(self) -> None:
        """
        All placetype values should be lowercase.
        """

        for pt in Placetype:
            assert pt.value == pt.value.lower()

    def test_placetype_from_string(self) -> None:
        """
        Placetype can be instantiated from a string.
        """

        assert Placetype('town') == Placetype.TOWN
        assert Placetype('country') == Placetype.COUNTRY

    def test_invalid_placetype_raises(self) -> None:
        """
        Invalid placetype string should raise ValueError.
        """

        with pytest.raises(ValueError, match='nonexistent'):
            Placetype('nonexistent')


class TestPlacetypeMappings:
    """
    Tests for placetype ID mappings.
    """

    def test_placetype_by_id_has_all_placetypes(self) -> None:
        """
        PLACETYPE_BY_ID should contain all enum members.
        """

        enum_members = set(Placetype)
        mapped_members = set(PLACETYPE_BY_ID.values())
        assert enum_members == mapped_members

    def test_placetype_id_is_reverse_of_by_id(self) -> None:
        """
        PLACETYPE_ID should be the reverse of PLACETYPE_BY_ID.
        """

        for ptid, pt in PLACETYPE_BY_ID.items():
            assert PLACETYPE_ID[pt] == ptid

    def test_placetype_country_constant(self) -> None:
        """
        PLACETYPE_COUNTRY should be 12.
        """

        assert PLACETYPE_COUNTRY == EXPECTED_COUNTRY_ID
        assert PLACETYPE_ID[Placetype.COUNTRY] == EXPECTED_COUNTRY_ID

    def test_placetype_unknown_constant(self) -> None:
        """
        PLACETYPE_UNKNOWN should be 0.
        """

        assert PLACETYPE_UNKNOWN == EXPECTED_UNKNOWN_ID

    @pytest.mark.parametrize(
        ('ptid', 'expected'),
        [
            (6, Placetype.STREET),
            (7, Placetype.TOWN),
            (8, Placetype.STATE),
            (9, Placetype.COUNTY),
            (12, Placetype.COUNTRY),
            (29, Placetype.CONTINENT),
            (37, Placetype.OCEAN),
            (38, Placetype.SEA),
        ],
    )
    def test_known_id_mappings(self, ptid: int, expected: Placetype) -> None:
        """
        Known placetype IDs should map to correct enum values.
        """

        assert PLACETYPE_BY_ID[ptid] == expected


class TestPlacetypeIdToShortname:
    """
    Tests for placetype_id_to_shortname function.
    """

    def test_valid_id_returns_placetype(self) -> None:
        """
        Valid ID should return Placetype enum value.
        """

        result = placetype_id_to_shortname(7)
        assert result == Placetype.TOWN
        assert result == 'town'

    def test_invalid_id_returns_none(self) -> None:
        """
        Invalid ID should return None.
        """

        assert placetype_id_to_shortname(999) is None
        assert placetype_id_to_shortname(0) is None
        assert placetype_id_to_shortname(-1) is None

    @pytest.mark.parametrize(
        ('ptid', 'expected'),
        [
            (12, 'country'),
            (7, 'town'),
            (8, 'state'),
            (22, 'suburb'),
        ],
    )
    def test_id_to_shortname_values(self, ptid: int, expected: str) -> None:
        """
        ID should map to correct shortname string.
        """

        assert placetype_id_to_shortname(ptid) == expected


class TestPlacetypeShortnameToId:
    """
    Tests for placetype_shortname_to_id function.
    """

    def test_valid_shortname_returns_id(self) -> None:
        """
        Valid shortname should return ID.
        """

        assert placetype_shortname_to_id('town') == EXPECTED_TOWN_ID

    def test_case_insensitive(self) -> None:
        """
        Shortname lookup should be case-insensitive.
        """

        assert placetype_shortname_to_id('TOWN') == EXPECTED_TOWN_ID
        assert placetype_shortname_to_id('Town') == EXPECTED_TOWN_ID
        assert placetype_shortname_to_id('tOwN') == EXPECTED_TOWN_ID

    def test_invalid_shortname_returns_none(self) -> None:
        """
        Invalid shortname should return None.
        """

        assert placetype_shortname_to_id('nonexistent') is None
        assert placetype_shortname_to_id('') is None

    @pytest.mark.parametrize(
        ('shortname', 'expected'),
        [
            ('country', 12),
            ('town', 7),
            ('state', 8),
            ('suburb', 22),
            ('continent', 29),
        ],
    )
    def test_shortname_to_id_values(self, shortname: str, expected: int) -> None:
        """
        Shortname should map to correct ID.
        """

        assert placetype_shortname_to_id(shortname) == expected
