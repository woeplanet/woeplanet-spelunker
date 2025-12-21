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

    @classmethod
    async def get_by_id(cls, db: Database, ptid: int) -> dict[str, Any] | None:
        """
        Get a placetype by ID
        """

        if cls._by_id is None:
            placetypes = await db.get_placetypes()
            cls._by_id = {pt['id']: pt for pt in placetypes}

        return cls._by_id.get(ptid)


async def placetype_by_id(db: Database, ptid: int) -> dict[str, Any] | None:
    """
    Get a placetype by ID
    """

    return await PlacetypeCache.get_by_id(db, ptid)
