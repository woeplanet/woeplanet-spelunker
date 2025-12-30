"""
WOEplanet Spelunker: common package; path parameters module.
"""

from http import HTTPStatus
from typing import Annotated

from pydantic import Field, TypeAdapter, ValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request

MAX_WOEID = 2_147_483_647
WOEID_REQUIRED = 'WOEID is required'
WOEID_INVALID = 'WOEID must be a positive 32-bit integer'
ISO_REQUIRED = 'ISO country code is required'
ISO_INVALID = 'ISO country code must be 2 uppercase letters'
PLACETYPE_REQUIRED = 'Placetype is required'
PLACETYPE_INVALID = 'Placetype must be a non-empty string'

WoeidType = Annotated[int, Field(gt=0, le=MAX_WOEID)]
IsoCountryCodeType = Annotated[str, Field(min_length=2, max_length=2, pattern=r'^[A-Z]{2}$')]
PlacetypeType = Annotated[str, Field(min_length=1, max_length=64)]

_woeid_adapter = TypeAdapter(WoeidType)
_iso_adapter = TypeAdapter(IsoCountryCodeType)
_placetype_adapter = TypeAdapter(PlacetypeType)


def get_path_woeid(request: Request) -> int:
    """
    Get a WOEID from the path
    """

    raw_woeid = request.path_params.get('woeid')
    if raw_woeid is None:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=WOEID_REQUIRED)

    try:
        return _woeid_adapter.validate_python(int(raw_woeid))

    except ValidationError as exc:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=WOEID_INVALID) from exc


def get_path_iso_code(request: Request) -> str:
    """
    Get an ISO 3166-1 alpha-2 country code from the path
    """

    raw_iso = request.path_params.get('iso')
    if raw_iso is None:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=ISO_REQUIRED)

    try:
        return _iso_adapter.validate_python(raw_iso.upper())

    except ValidationError as exc:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=ISO_INVALID) from exc


def get_path_placetype(request: Request) -> str:
    """
    Get a short form placetype name from the path
    """

    raw_placetype = request.path_params.get('placetype')
    if raw_placetype is None:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=PLACETYPE_REQUIRED)

    try:
        return _placetype_adapter.validate_python(raw_placetype)

    except ValidationError as exc:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=PLACETYPE_INVALID) from exc
