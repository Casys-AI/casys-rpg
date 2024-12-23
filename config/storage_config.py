"""
Storage configuration module.
Centralized configuration for all storage-related settings.
"""

from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Dict, Optional, Any

class StorageFormat(str, Enum):
    """Storage format for data."""
    JSON = "json"
    MARKDOWN = "markdown"
    RAW = "raw"

class NamespaceConfig(BaseModel):
    """Configuration for a storage namespace."""
    path: Path = Field(
        description="Path relative to base_path where namespace data is stored"
    )
    format: StorageFormat = Field(
        description="Storage format for this namespace"
    )
    ttl_seconds: Optional[int] = Field(
        default=None,
        description="Cache TTL in seconds. None means no expiration"
    )
    cache_enabled: bool = Field(
        default=True,
        description="Whether to enable caching for this namespace"
    )
    per_game: bool = Field(
        default=False,
        description="Whether this namespace is per-game (stored in games/{game_id}/)"
    )

# Default namespace configurations
DEFAULT_NAMESPACES = {
    "state": NamespaceConfig(
        path=Path("cache/games/{game_id}/states"),
        format=StorageFormat.JSON,
        ttl_seconds=3600,
        per_game=True
    ),
    "trace": NamespaceConfig(
        path=Path("cache/games/{game_id}/traces"),
        format=StorageFormat.JSON,
        ttl_seconds=3600,
        per_game=True
    ),
    "character": NamespaceConfig(
        path=Path("cache/games/{game_id}/characters"),
        format=StorageFormat.MARKDOWN,
        per_game=True
    ),
    "rules": NamespaceConfig(
        path=Path("cache/rules"),
        format=StorageFormat.MARKDOWN,
        ttl_seconds=None
    ),
    "cached_sections": NamespaceConfig(
        path=Path("cache/sections"),
        format=StorageFormat.MARKDOWN,
        ttl_seconds=None
    ),
    "sections": NamespaceConfig(
        path=Path("sections"),  # Relatif à base_path (./data)
        format=StorageFormat.MARKDOWN,  # Les fichiers sont en markdown même si c'est la source
        ttl_seconds=None  # Pas de cache car c'est la source
    )
}

class StorageConfig(BaseModel):
    """Main storage configuration."""
    # Base storage settings
    base_path: Path = Field(
        default=Path("./data"),
        description="Base path for all storage operations"
    )
    encoding: str = Field(
        default="utf-8",
        description="Default file encoding"
    )
    max_cache_size: int = Field(
        default=1000,
        description="Maximum number of items in memory cache"
    )
    game_id: Optional[str] = Field(
        default=None,
        description="Current game ID for per-game namespaces"
    )
    
    # Manager settings from ManagerConfigBase
    manager_id: str = Field(
        default="",
        description="Unique identifier for the manager"
    )
    persistence_enabled: bool = Field(
        default=True,
        description="Enable data persistence"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    cache_enabled: bool = Field(
        default=True,
        description="Enable caching"
    )
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional options"
    )
    
    # Namespace configurations
    namespaces: Dict[str, NamespaceConfig] = Field(
        default_factory=lambda: DEFAULT_NAMESPACES.copy(),
        description="Configuration for each storage namespace"
    )

    def get_absolute_path(self, namespace: str) -> Path:
        """Get absolute path for a namespace."""
        if namespace not in self.namespaces:
            raise KeyError(f"Unknown namespace: {namespace}")
            
        path = self.namespaces[namespace].path
        if self.namespaces[namespace].per_game:
            if not self.game_id:
                raise ValueError(f"game_id must be set for per-game namespace: {namespace}")
            path = Path(str(path).format(game_id=self.game_id))
            
        return self.base_path / path

    @classmethod
    def get_default_config(cls, base_path: Path, game_id: Optional[str] = None) -> 'StorageConfig':
        """Get default storage configuration.
        
        Args:
            base_path: Base path for all storage
            game_id: Optional game ID for per-game namespaces
            
        Returns:
            StorageConfig: Default configuration
        """
        return cls(
            base_path=base_path,
            game_id=game_id,
            namespaces=DEFAULT_NAMESPACES.copy()
        )
