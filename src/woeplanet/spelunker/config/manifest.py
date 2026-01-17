"""
WOEplanet Spelunker: config package; manifest module.
"""

from functools import lru_cache

import yaml
from pydantic import BaseModel

from woeplanet.spelunker.config.settings import get_settings


class ManifestDatabase(BaseModel):
    """
    WOEplanet Spelunker manifest database.
    """

    db: str
    sum: str
    size: int


class ManifestPlacetype(BaseModel):
    """
    WOEplanet Spelunker manifest placetype.
    """

    name: str
    id: int
    places: ManifestDatabase
    geometries: ManifestDatabase


class Manifest(BaseModel):
    """
    WOEplanet Spelunker manifest.
    """

    meta: list[ManifestDatabase]
    placetypes: dict[str, ManifestPlacetype]


@lru_cache
def get_manifest() -> Manifest:
    """
    Get the WOEplanet Spelunker manifest.
    """

    settings = get_settings()
    with settings.woeplanet_downloads_manifest.open(mode='r', encoding='utf-8') as ifh:
        data = yaml.safe_load(ifh)
        return Manifest.model_validate(data)
