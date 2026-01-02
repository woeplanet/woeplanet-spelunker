"""
WOEplanet Spelunker: tests package; FTS sanitisation tests.
"""

import pytest

from woeplanet.spelunker.common.query_params import sanitise_name_search_query


class TestSanitiseNameSearchQuery:
    """
    Tests for the FTS query sanitisation function.
    """

    def test_empty_query_returns_none(self) -> None:
        """
        Empty query should return None.
        """

        assert sanitise_name_search_query('') is None
        assert sanitise_name_search_query('   ') is None

    def test_simple_query_unchanged(self) -> None:
        """
        Simple query should be returned unchanged.
        """

        assert sanitise_name_search_query('London') == 'London'
        assert sanitise_name_search_query('New York') == 'New York'

    def test_strips_column_specifier(self) -> None:
        """
        Column specifier (:) should be stripped.
        """

        assert sanitise_name_search_query('name:London') == 'nameLondon'

    def test_strips_boost_operator(self) -> None:
        """
        Boost operator (^) should be stripped.
        """

        assert sanitise_name_search_query('London^2') == 'London2'

    def test_preserves_fts_operators(self) -> None:
        """
        FTS operators should be preserved.
        """

        assert sanitise_name_search_query('London AND Paris') == 'London AND Paris'
        assert sanitise_name_search_query('London OR Paris') == 'London OR Paris'
        assert sanitise_name_search_query('NOT London') == 'NOT London'

    def test_preserves_quoted_phrases(self) -> None:
        """
        Quoted phrases should be preserved.
        """

        assert sanitise_name_search_query('"New York"') == '"New York"'

    def test_balances_unmatched_quotes(self) -> None:
        """
        Unmatched quotes should be removed to prevent FTS syntax errors.
        """

        assert sanitise_name_search_query('"London') == 'London'
        assert sanitise_name_search_query('London"') == 'London'

    def test_preserves_prefix_matching(self) -> None:
        """
        Prefix matching (*) should be preserved.
        """

        assert sanitise_name_search_query('Lond*') == 'Lond*'

    @pytest.mark.parametrize(
        ('query', 'expected'),
        [
            ('  London  ', 'London'),
            ('\tParis\n', 'Paris'),
        ],
    )
    def test_strips_whitespace(self, query: str, expected: str) -> None:
        """
        Leading/trailing whitespace should be stripped.
        """

        assert sanitise_name_search_query(query) == expected
