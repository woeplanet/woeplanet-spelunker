"""
WOEplanet Spelunker: tests package; languages module tests.
"""

import pytest

from woeplanet.spelunker.common.languages import language_name


class TestLanguageName:
    """
    Tests for the language_name function.
    """

    def test_unknown_code_returns_unknown(self) -> None:
        """
        Unknown language code should return 'Unknown'.
        """

        assert language_name('UNK') == 'Unknown'
        assert language_name('unk') == 'Unknown'

    def test_valid_alpha3_code(self) -> None:
        """
        Valid ISO 639 alpha-3 code should return language name.
        """

        assert language_name('eng') == 'English'
        assert language_name('ENG') == 'English'

    def test_valid_bibliographic_code(self) -> None:
        """
        Valid bibliographic code should return language name.
        """

        assert language_name('ger') == 'German'
        assert language_name('fre') == 'French'

    def test_invalid_code_returns_unknown(self) -> None:
        """
        Invalid language code should return 'Unknown'.
        """

        assert language_name('xxx') == 'Unknown'
        assert language_name('zzz') == 'Unknown'

    @pytest.mark.parametrize(
        ('code', 'expected'),
        [
            ('spa', 'Spanish'),
            ('ita', 'Italian'),
            ('por', 'Portuguese'),
            ('jpn', 'Japanese'),
            ('zho', 'Chinese'),
        ],
    )
    def test_common_languages(self, code: str, expected: str) -> None:
        """
        Common language codes should return correct names.
        """

        assert language_name(code) == expected
