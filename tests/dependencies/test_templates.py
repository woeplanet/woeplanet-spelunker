"""
WOEplanet Spelunker: tests package; template filter tests.
"""

from http import HTTPStatus

import pytest

from woeplanet.spelunker.dependencies.templates import (
    any_filter,
    comma_filter,
    http_description_filter,
    http_phrase_filter,
    name_type_filter,
    plural_filter,
)


class TestPluralFilter:
    """
    Tests for the plural_filter function.
    """

    def test_empty_value_unchanged(self) -> None:
        """
        Empty value should be returned unchanged.
        """

        assert plural_filter('') == ''

    def test_simple_plural(self) -> None:
        """
        Simple word should be pluralised.
        """

        assert plural_filter('town') == 'towns'
        assert plural_filter('country') == 'countries'

    def test_phrase_plural(self) -> None:
        """
        Phrase should have first noun pluralised.
        """

        result = plural_filter('Point of Interest')
        assert 'Points' in result

    def test_with_count(self) -> None:
        """
        Count parameter should influence pluralisation.
        """

        assert plural_filter('town', 1) == 'town'
        assert plural_filter('town', 2) == 'towns'


class TestAnyFilter:
    """
    Tests for the any_filter (a/an) function.
    """

    def test_consonant_start(self) -> None:
        """
        Word starting with consonant should get 'a'.
        """

        assert any_filter('town').startswith('a ')

    def test_vowel_start(self) -> None:
        """
        Word starting with vowel should get 'an'.
        """

        assert any_filter('island').startswith('an ')

    def test_miscellaneous_unchanged(self) -> None:
        """
        'miscellaneous' should be returned unchanged.
        """

        assert any_filter('miscellaneous') == 'miscellaneous'
        assert any_filter('Miscellaneous') == 'Miscellaneous'


class TestHttpPhraseFilter:
    """
    Tests for the http_phrase_filter function.
    """

    def test_ok_status(self) -> None:
        """
        200 should return 'OK'.
        """

        assert http_phrase_filter(200) == 'OK'

    def test_not_found_status(self) -> None:
        """
        404 should return 'Not Found'.
        """

        assert http_phrase_filter(404) == 'Not Found'

    def test_internal_server_error_status(self) -> None:
        """
        500 should return 'Internal Server Error'.
        """

        assert http_phrase_filter(500) == 'Internal Server Error'


class TestHttpDescriptionFilter:
    """
    Tests for the http_description_filter function.
    """

    def test_ok_description(self) -> None:
        """
        200 should return appropriate description.
        """

        assert 'Request fulfilled' in http_description_filter(HTTPStatus.OK)

    def test_not_found_description(self) -> None:
        """
        404 should return appropriate description.
        """

        assert 'Nothing matches' in http_description_filter(HTTPStatus.NOT_FOUND)


class TestCommaFilter:
    """
    Tests for the comma_filter function.
    """

    def test_small_number(self) -> None:
        """
        Small numbers should be unchanged.
        """

        assert comma_filter(100) == '100'

    def test_thousands(self) -> None:
        """
        Thousands should have comma separator.
        """

        assert comma_filter(1000) == '1,000'

    def test_millions(self) -> None:
        """
        Millions should have comma separators.
        """

        assert comma_filter(1000000) == '1,000,000'

    @pytest.mark.parametrize(
        ('value', 'expected'),
        [
            (0, '0'),
            (999, '999'),
            (1234, '1,234'),
            (12345, '12,345'),
            (123456789, '123,456,789'),
        ],
    )
    def test_various_numbers(self, value: int, expected: str) -> None:
        """
        Various numbers should be formatted correctly.
        """

        assert comma_filter(value) == expected


class TestNameTypeFilter:
    """
    Tests for the name_type_filter function.
    """

    @pytest.mark.parametrize(
        ('code', 'expected'),
        [
            ('S', 'standard'),
            ('P', 'preferred'),
            ('V', 'variant'),
            ('Q', 'colloquial'),
            ('A', 'abbreviated'),
        ],
    )
    def test_known_name_types(self, code: str, expected: str) -> None:
        """
        Known name type codes should return correct descriptions.
        """

        assert name_type_filter(code) == expected

    def test_unknown_name_type(self) -> None:
        """
        Unknown name type should return 'unknown'.
        """

        assert name_type_filter('X') == 'unknown'
        assert name_type_filter('') == 'unknown'

