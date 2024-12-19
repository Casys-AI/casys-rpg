"""Cache Manager configuration."""
from typing import Dict, Any
from pydantic import Field

from config.managers.manager_config_base import ManagerConfigBase

class CacheManagerConfig(ManagerConfigBase):
    """Configuration for the Cache Manager."""
    
    # Cache settings
    max_size: int = Field(
        default=1000,
        description="Maximum number of items in cache"
    )
    ttl_seconds: int = Field(
        default=3600,
        description="Time-to-live for cache items in seconds"
    )
    
    # Storage settings
    storage_path: str = Field(
        default="cache",
        description="Path for cache storage"
    )
    compression_enabled: bool = Field(
        default=True,
        description="Enable compression for cached data"
    )
