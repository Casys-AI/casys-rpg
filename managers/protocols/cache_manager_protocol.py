"""
Cache Manager Protocol
Defines the interface for caching operations.
"""
from typing import Optional, Any, Dict, Protocol, runtime_checkable, Type, TypeVar, List
from pydantic import BaseModel
from abc import abstractmethod

T = TypeVar('T', bound=BaseModel)

@runtime_checkable
class CacheManagerProtocol(Protocol):
    """Protocol defining the interface for caching operations."""
    
    @abstractmethod
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
    
    @abstractmethod
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
    
    @abstractmethod
    async def clear_namespace_cache(self, namespace: str) -> None:
        """
        Clear all cached data for a specific namespace.
        
        Args:
            namespace: Namespace to clear
            
        Raises:
            KeyError: If namespace is unknown
        """
        ...
    
    @abstractmethod
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
    
    @abstractmethod
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
    
    @abstractmethod
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
    
    @abstractmethod
    async def list_keys(self, namespace: str, pattern: str) -> List[str]:
        """
        List all keys in a namespace matching a pattern.
        
        Args:
            namespace: Namespace to search in
            pattern: Pattern to match (glob style)
            
        Returns:
            List[str]: List of matching keys
            
        Raises:
            KeyError: If namespace is unknown
        """
        ...
        
    @abstractmethod
    async def clear_pattern(self, namespace: str, pattern: str) -> None:
        """
        Clear all cached data matching a pattern in a namespace.
        
        Args:
            namespace: Namespace to clear in
            pattern: Pattern to match (glob style)
            
        Raises:
            KeyError: If namespace is unknown
        """
        ...
    
    @abstractmethod
    async def update_game_id(self, game_id: str) -> None:
        """Update the game ID for per-game namespaces.
        
        Args:
            game_id: New game ID to use
        """
        pass
