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

    woeplanet_host: str
    woeplanet_port: int

    woeplanet_config_dir: DirectoryPath
    woeplanet_static_dir: DirectoryPath
    woeplanet_templates_dir: DirectoryPath
    woeplanet_storage_dir: DirectoryPath
    woeplanet_downloads_dir: DirectoryPath
    woeplanet_cache_dir: DirectoryPath
    woeplanet_db_path: FilePath
    woeplanet_geom_db_path: FilePath
    woeplanet_downloads_manifest: FilePath

    woeplanet_logging_config: FilePath
    woeplanet_log_level: Literal['trace', 'debug', 'info', 'warning', 'error', 'critical']

    woeplanet_cache_ttl: int = DEFAULT_CACHE_TTL
    woeplanet_nearby_distance: int = DEFAULT_NEARBY_DISTANCE

    @field_validator('woeplanet_db_path', 'woeplanet_geom_db_path', mode='after')
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
