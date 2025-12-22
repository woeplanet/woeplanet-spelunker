"""
WOEplanet Spelunker: config package; placetypes module.
"""

from typing import Any

from woeplanet.spelunker.dependencies.database import Database


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


async def placetype_by_id(db: Database, ptid: int) -> dict[str, Any] | None:
    """
    Get a placetype by ID
    """

    return await PlacetypeCache.get_by_id(db, ptid)


async def placetype_by_shortname(db: Database, shortname: str) -> dict[str, Any] | None:
    """
    Get a placetype by shortname (case-insensitive)
    """

    return await PlacetypeCache.get_by_shortname(db, shortname)
