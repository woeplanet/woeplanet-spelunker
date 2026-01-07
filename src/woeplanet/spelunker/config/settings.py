"""
WOEplanet Spelunker: config package; settings module.
"""

from functools import lru_cache
from typing import Literal

import dotenv
from pydantic import DirectoryPath, FilePath, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CACHE_TTL = 3600  # 1 hour
DEFAULT_NEARBY_DISTANCE = 5000  # 5 km


class Settings(BaseSettings):
    """
    WOEplanet Spelunker .env settings.
    """

    model_config = SettingsConfigDict(env_file=dotenv.find_dotenv(), env_file_encoding='utf-8', extra='ignore')

    host: str
    port: int

    config_dir: DirectoryPath
    static_dir: DirectoryPath
    templates_dir: DirectoryPath
    storage_dir: DirectoryPath
    downloads_dir: DirectoryPath
    cache_dir: DirectoryPath
    db_path: FilePath
    geom_db_path: FilePath
    downloads_manifest: FilePath

    logging_config: FilePath
    log_level: Literal['trace', 'debug', 'info', 'warning', 'error', 'critical']

    cache_ttl: int = DEFAULT_CACHE_TTL
    nearby_distance: int = DEFAULT_NEARBY_DISTANCE

    @field_validator('db_path', 'geom_db_path', mode='after')
    @classmethod
    def _make_absolute(cls, value: FilePath) -> FilePath:
        """
        Expand paths to absolute paths.
        """

        return value.resolve()


@lru_cache
def get_settings() -> Settings:
    """
    Find and return settings in the current .env file.
    """

    return Settings()
