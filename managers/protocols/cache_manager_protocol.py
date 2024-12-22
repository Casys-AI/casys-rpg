"""
Cache Manager Protocol
Defines the interface for caching operations.
"""
from typing import Protocol, Optional, Any, Dict, runtime_checkable
from .base_protocols import CacheProtocol

@runtime_checkable
class CacheManagerProtocol(CacheProtocol):
    """Protocol defining the interface for caching operations."""
    
    def initialize(self) -> None:
        """Initialize the cache manager."""
        ...
    
    async def save_cached_content(self, key: str, namespace: str, data: Any) -> bool:
        """
        Save content to cache.
        
        Args:
            key: Cache key
            namespace: Cache namespace
            data: Data to cache
            
        Returns:
            bool: True if save was successful
        """
        ...
    
    async def get_cached_content(self, key: str, namespace: str) -> Optional[Any]:
        """
        Get content from cache.
        
        Args:
            key: Cache key
            namespace: Cache namespace
            
        Returns:
            Optional[Any]: Cached content if found
        """
        ...
    
    async def get_cached_content(self, key: str) -> Optional[str]:
        """Get cached content by key."""
        ...
    
    async def save_cached_content(self, key: str, content: str) -> bool:
        """Save content to cache."""
        ...
    
    def exists_raw_content(self, section_number: int, namespace: str) -> bool:
        """
        Check if raw content exists.
        
        Args:
            section_number: Section number to check
            namespace: Namespace to check in
            
        Returns:
            bool: True if exists
        """
        ...
    
    async def load_raw_content(self, section_number: int, namespace: str) -> Optional[str]:
        """
        Load raw content.
        
        Args:
            section_number: Section number to load
            namespace: Namespace to load from
            
        Returns:
            Optional[str]: Raw content if found
        """
        ...
    
    async def load_raw_content(self, key: str) -> Optional[str]:
        """Load raw content by key."""
        ...
    
    async def delete_cached_content(self, key: str, namespace: str) -> bool:
        """
        Delete content from cache.
        
        Args:
            key: Cache key
            namespace: Cache namespace
            
        Returns:
            bool: True if delete was successful
        """
        ...
    
    async def clear_namespace(self, namespace: str) -> bool:
        """
        Clear all content in a namespace.
        
        Args:
            namespace: Cache namespace to clear
            
        Returns:
            bool: True if clear was successful
        """
        ...
    
    def clear_cache(self) -> None:
        """Clear all cached content."""
        ...
