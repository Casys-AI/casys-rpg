"""Base protocols for managers."""
from typing import Protocol, Dict, Any, Optional

class BaseProtocol(Protocol):
    """Base protocol class for all managers in the system.
    
    This protocol defines the foundational interface that all manager protocols
    must implement. It serves as a root protocol in the protocol hierarchy,
    ensuring consistency across different types of managers.
    """
    ...

class StorageProtocol(BaseProtocol):
    """Base protocol for storage-based managers."""
    
    def get_storage_path(self) -> str:
        """Get storage path."""
        ...
    
    def get_storage_options(self) -> Dict[str, Any]:
        """Get storage options."""
        ...

class CacheProtocol(BaseProtocol):
    """Base protocol for cache-based managers."""
    
    def get_cache_enabled(self) -> bool:
        """Get if caching is enabled."""
        ...
    
    def get_cache_options(self) -> Dict[str, Any]:
        """Get cache options."""
        ...
