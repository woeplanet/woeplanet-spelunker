"""
WOEplanet Spelunker: config package; placetypes module.
"""

from enum import StrEnum
from typing import Any

from woeplanet.spelunker.dependencies.database import Database

PLACETYPE_UNKNOWN = 0


class Placetype(StrEnum):
    """
    WOE placetype shortnames.
    """

    STREET = 'street'
    TOWN = 'town'
    STATE = 'state'
    COUNTY = 'county'
    LOCAL_ADMIN = 'localadmin'
    ZIP = 'zip'
    COUNTRY = 'country'
    ISLAND = 'island'
    AIRPORT = 'airport'
    DRAINAGE = 'drainage'
    LAND_FEATURE = 'landfeature'
    MISCELLANEOUS = 'miscellaneous'
    NATIONALITY = 'nationality'
    SUPERNAME = 'supername'
    POI = 'poi'
    REGION = 'region'
    SUBURB = 'suburb'
    SPORTS_TEAM = 'sportsteam'
    COLLOQUIAL = 'colloquial'
    ZONE = 'zone'
    HISTORICAL_STATE = 'historicalstate'
    HISTORICAL_COUNTY = 'historicalcounty'
    CONTINENT = 'continent'
    TIMEZONE = 'timezone'
    NEARBY_INTERSECTION = 'nearbyintersection'
    ESTATE = 'estate'
    HISTORICAL_TOWN = 'historicaltown'
    AGGREGATE = 'aggregate'
    OCEAN = 'ocean'
    SEA = 'sea'


PLACETYPE_BY_ID: dict[int, Placetype] = {
    6: Placetype.STREET,
    7: Placetype.TOWN,
    8: Placetype.STATE,
    9: Placetype.COUNTY,
    10: Placetype.LOCAL_ADMIN,
    11: Placetype.ZIP,
    12: Placetype.COUNTRY,
    13: Placetype.ISLAND,
    14: Placetype.AIRPORT,
    15: Placetype.DRAINAGE,
    16: Placetype.LAND_FEATURE,
    17: Placetype.MISCELLANEOUS,
    18: Placetype.NATIONALITY,
    19: Placetype.SUPERNAME,
    20: Placetype.POI,
    21: Placetype.REGION,
    22: Placetype.SUBURB,
    23: Placetype.SPORTS_TEAM,
    24: Placetype.COLLOQUIAL,
    25: Placetype.ZONE,
    26: Placetype.HISTORICAL_STATE,
    27: Placetype.HISTORICAL_COUNTY,
    29: Placetype.CONTINENT,
    31: Placetype.TIMEZONE,
    32: Placetype.NEARBY_INTERSECTION,
    33: Placetype.ESTATE,
    35: Placetype.HISTORICAL_TOWN,
    36: Placetype.AGGREGATE,
    37: Placetype.OCEAN,
    38: Placetype.SEA,
}

PLACETYPE_ID: dict[Placetype, int] = {v: k for k, v in PLACETYPE_BY_ID.items()}

PLACETYPE_COUNTRY = PLACETYPE_ID[Placetype.COUNTRY]


class PlacetypeCache:
    """
    Cache for placetype lookups by ID.
    """

    _by_id: dict[int, dict[str, Any]] | None = None
    _by_shortname: dict[str, dict[str, Any]] | None = None

    @classmethod
    async def _populate(cls, db: Database) -> None:
        """
        Populate the cache from the database.
        """

        if cls._by_id is None:
            placetypes = await db.get_placetypes()
            cls._by_id = {pt['id']: pt for pt in placetypes}
            cls._by_shortname = {pt['shortname'].lower(): pt for pt in placetypes}

    @classmethod
    async def get_by_id(cls, db: Database, ptid: int) -> dict[str, Any] | None:
        """
        Get a placetype by ID
        """

        await cls._populate(db)
        return cls._by_id.get(ptid) if cls._by_id else None

    @classmethod
    async def get_by_shortname(cls, db: Database, shortname: str) -> dict[str, Any] | None:
        """
        Get a placetype by shortname (case-insensitive)
        """

        await cls._populate(db)
        return cls._by_shortname.get(shortname.lower()) if cls._by_shortname else None


def placetype_id_to_shortname(ptid: int) -> Placetype | None:
    """
    Get a placetype shortname by ID without database access.
    """

    return PLACETYPE_BY_ID.get(ptid)


def placetype_shortname_to_id(shortname: str) -> int | None:
    """
    Get a placetype ID by shortname without database access.
    """

    try:
        pt = Placetype(shortname.lower())
        return PLACETYPE_ID.get(pt)
    except ValueError:
        return None


async def placetype_by_id(db: Database, ptid: int) -> dict[str, Any] | None:
    """
    Get a placetype record by ID.

    Returns full database record including name and description.
    """

    if ptid not in PLACETYPE_BY_ID:
        return None

    return await PlacetypeCache.get_by_id(db, ptid)


async def placetype_by_shortname(db: Database, shortname: str) -> dict[str, Any] | None:
    """
    Get a placetype record by shortname (case-insensitive).

    Returns full database record including name and description.
    """

    try:
        Placetype(shortname.lower())
    except ValueError:
        return None

    return await PlacetypeCache.get_by_shortname(db, shortname)
