"""
Cache Manager Protocol
Defines the interface for caching operations.
"""
from typing import Optional, Any, Dict, Protocol, runtime_checkable, Type, TypeVar
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

@runtime_checkable
class CacheManagerProtocol(Protocol):
    """Protocol defining the interface for caching operations."""
    
    async def save_cached_data(self, key: str, namespace: str, data: Any) -> None:
        """
        Save data to both cache and persistent storage.
        
        Args:
            key: Unique identifier for the data
            namespace: Namespace for organizing data
            data: Data to save (can be any serializable type)
        
        Raises:
            KeyError: If namespace is unknown
            Exception: If save operation fails
        """
        ...
    
    async def get_cached_data(self, key: str, namespace: str, model_type: Optional[Type[T]] = None) -> Optional[Any]:
        """
        Get data from cache or persistent storage.
        
        Args:
            key: Unique identifier for the data
            namespace: Namespace for organizing data
            model_type: Optional Pydantic model type for deserialization
            
        Returns:
            Optional[Any]: Retrieved data, or None if not found
            
        Raises:
            KeyError: If namespace is unknown
        """
        ...
    
    async def clear_namespace_cache(self, namespace: str) -> None:
        """
        Clear all cached data for a specific namespace.
        
        Args:
            namespace: Namespace to clear
            
        Raises:
            KeyError: If namespace is unknown
        """
        ...
    
    async def save_cached_content(self, key: str, namespace: str, data: Any) -> None:
        """
        Save content to cache.
        
        Args:
            key: Cache key
            namespace: Cache namespace
            data: Data to cache
            
        Raises:
            KeyError: If namespace is unknown
            Exception: If save operation fails
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
            
        Raises:
            KeyError: If namespace is unknown
        """
        ...
    
    async def exists_raw_content(self, key: str, namespace: str) -> bool:
        """
        Check if raw content exists in cache or storage.
        
        Args:
            key: Unique identifier for the content
            namespace: Namespace for organizing data
            
        Returns:
            bool: True if content exists, False otherwise
            
        Raises:
            KeyError: If namespace is unknown
        """
        ...
    
    async def load_raw_content(self, key: str, namespace: str) -> Optional[str]:
        """
        Load raw content from storage.
        
        Args:
            key: Unique identifier for the content
            namespace: Namespace for organizing data
            
        Returns:
            Optional[str]: Content if found, None otherwise
            
        Raises:
            KeyError: If namespace is unknown
        """
        ...
    
    async def delete_cached_content(self, key: str, namespace: str) -> None:
        """
        Delete content from cache.
        
        Args:
            key: Cache key
            namespace: Cache namespace
            
        Raises:
            KeyError: If namespace is unknown
        """
        ...
