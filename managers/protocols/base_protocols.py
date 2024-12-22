"""Base protocols for managers."""
from typing import Protocol, Dict, Any, Optional

class StorageProtocol(Protocol):
    """Base protocol for storage-based managers."""
    
    def get_storage_path(self) -> str:
        """Get storage path."""
        ...
    
    def get_storage_options(self) -> Dict[str, Any]:
        """Get storage options."""
        ...

class CacheProtocol(Protocol):
    """Base protocol for cache-based managers."""
    
    def get_cache_enabled(self) -> bool:
        """Get if caching is enabled."""
        ...
    
    def get_cache_options(self) -> Dict[str, Any]:
        """Get cache options."""
        ...
