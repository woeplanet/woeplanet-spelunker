"""
WOEplanet Spelunker: tests package; path parameters tests.
"""

from http import HTTPStatus
from unittest.mock import MagicMock

import pytest
from starlette.exceptions import HTTPException

from woeplanet.spelunker.common.path_params import (
    MAX_WOEID,
    get_iso_country_code,
    get_placetype,
    get_woeid,
)


class TestGetWoeid:
    """
    Tests for the get_woeid function.
    """

    def test_valid_woeid(self) -> None:
        """
        Valid WOEID should be returned as int.
        """

        request = MagicMock()
        request.path_params = {'woeid': 44418}
        assert get_woeid(request) == 44418

    def test_missing_woeid_raises(self) -> None:
        """
        Missing WOEID should raise HTTPException.
        """

        request = MagicMock()
        request.path_params = {}

        with pytest.raises(HTTPException) as exc_info:
            get_woeid(request)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST

    def test_negative_woeid_raises(self) -> None:
        """
        Negative WOEID should raise HTTPException.
        """

        request = MagicMock()
        request.path_params = {'woeid': -1}

        with pytest.raises(HTTPException) as exc_info:
            get_woeid(request)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST

    def test_zero_woeid_raises(self) -> None:
        """
        Zero WOEID should raise HTTPException.
        """

        request = MagicMock()
        request.path_params = {'woeid': 0}

        with pytest.raises(HTTPException) as exc_info:
            get_woeid(request)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST

    def test_woeid_exceeds_max_raises(self) -> None:
        """
        WOEID exceeding max should raise HTTPException.
        """

        request = MagicMock()
        request.path_params = {'woeid': MAX_WOEID + 1}

        with pytest.raises(HTTPException) as exc_info:
            get_woeid(request)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST


class TestGetIsoCountryCode:
    """
    Tests for the get_iso_country_code function.
    """

    def test_valid_iso_uppercase(self) -> None:
        """
        Valid uppercase ISO code should be returned.
        """

        request = MagicMock()
        request.path_params = {'iso': 'GB'}
        assert get_iso_country_code(request) == 'GB'

    def test_valid_iso_lowercase_converted(self) -> None:
        """
        Lowercase ISO code should be converted to uppercase.
        """

        request = MagicMock()
        request.path_params = {'iso': 'gb'}
        assert get_iso_country_code(request) == 'GB'

    def test_missing_iso_raises(self) -> None:
        """
        Missing ISO code should raise HTTPException.
        """

        request = MagicMock()
        request.path_params = {}

        with pytest.raises(HTTPException) as exc_info:
            get_iso_country_code(request)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST

    def test_invalid_iso_length_raises(self) -> None:
        """
        ISO code with wrong length should raise HTTPException.
        """

        request = MagicMock()
        request.path_params = {'iso': 'GBR'}

        with pytest.raises(HTTPException) as exc_info:
            get_iso_country_code(request)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST


class TestGetPlacetype:
    """
    Tests for the get_placetype function.
    """

    def test_valid_placetype(self) -> None:
        """
        Valid placetype should be returned.
        """

        request = MagicMock()
        request.path_params = {'placetype': 'town'}
        assert get_placetype(request) == 'town'

    def test_missing_placetype_raises(self) -> None:
        """
        Missing placetype should raise HTTPException.
        """

        request = MagicMock()
        request.path_params = {}

        with pytest.raises(HTTPException) as exc_info:
            get_placetype(request)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST

    def test_empty_placetype_raises(self) -> None:
        """
        Empty placetype should raise HTTPException.
        """

        request = MagicMock()
        request.path_params = {'placetype': ''}

        with pytest.raises(HTTPException) as exc_info:
            get_placetype(request)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST

