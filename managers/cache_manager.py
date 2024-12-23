"""
Cache Manager Module
Handles caching and persistence of game data through a unified interface.
"""

from typing import Dict, Optional, Any, Union, Type, TypeVar
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json
from pydantic import BaseModel

from config.storage_config import StorageConfig, StorageFormat
from managers.filesystem_adapter import FileSystemAdapter
from managers.protocols.cache_manager_protocol import CacheManagerProtocol

T = TypeVar('T', bound=BaseModel)

# Mapping of storage formats to file extensions
_FORMAT_TO_EXTENSION = {
    StorageFormat.JSON: ".json",
    StorageFormat.MARKDOWN: ".md",
    StorageFormat.RAW: ".md"
}

def _json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, timedelta)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

class CacheEntry:
    """Represents a cached item with TTL."""
    def __init__(self, value: Any, ttl_seconds: Optional[int]):
        self.value = value
        self.expiry = datetime.now() + timedelta(seconds=ttl_seconds) if ttl_seconds else None
        
    def is_expired(self) -> bool:
        return self.expiry and datetime.now() > self.expiry

class CacheManager(CacheManagerProtocol):
    """
    Manages caching and persistence of game data.
    Provides a unified interface for other managers to store and retrieve data.
    """
    
    def __init__(self, config: StorageConfig):
        """Initialize CacheManager with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._fs_adapter = FileSystemAdapter(config)
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._current_session: Optional[Path] = None

    def _get_cache_key(self, key: str, namespace: str) -> str:
        """Generate a unique cache key."""
        return f"{namespace}:{key}"

    def _get_file_extension(self, namespace: str) -> str:
        """Get file extension for namespace."""
        format = self.config.namespaces[namespace].format
        return _FORMAT_TO_EXTENSION[format]

    def _serialize_data(self, data: Any, namespace: str) -> str:
        """Serialize data according to namespace format."""
        format = self.config.namespaces[namespace].format
        
        if format == StorageFormat.JSON:
            if isinstance(data, BaseModel):
                data_dict = data.model_dump()
                return json.dumps(data_dict, default=_json_serial)
            return json.dumps(data, default=_json_serial)
        elif format == StorageFormat.MARKDOWN:
            if hasattr(data, 'to_markdown'):
                return data.to_markdown()
            elif isinstance(data, BaseModel):
                return self._model_to_markdown(data)
            else:
                return str(data)
        else:  # RAW
            return str(data)

    def _deserialize_data(self, data: str, namespace: str, model_type: Optional[Type[T]] = None) -> Any:
        """Deserialize data according to namespace format."""
        format = self.config.namespaces[namespace].format
        
        if format == StorageFormat.JSON:
            json_data = json.loads(data)
            if model_type:
                return model_type.model_validate(json_data)
            return json_data
        elif format == StorageFormat.MARKDOWN:
            if model_type and hasattr(model_type, 'from_markdown'):
                return model_type.from_markdown(data)
            return data
        else:  # RAW
            return data

    def _model_to_markdown(self, model: BaseModel) -> str:
        """Convert a Pydantic model to markdown format."""
        lines = [f"# {model.__class__.__name__}"]
        
        for field_name, field_value in model.model_dump().items():
            if isinstance(field_value, (list, dict)):
                lines.append(f"\n## {field_name}")
                if isinstance(field_value, list):
                    for item in field_value:
                        lines.append(f"- {item}")
                else:
                    for key, value in field_value.items():
                        lines.append(f"- {key}: {value}")
            else:
                lines.append(f"- {field_name}: {field_value}")
        
        return "\n".join(lines)

    async def save_cached_data(self, key: str, namespace: str, data: Any) -> None:
        """Save data to both cache and persistent storage."""
        try:
            if namespace not in self.config.namespaces:
                raise KeyError(f"Unknown namespace: {namespace}")
                
            ns_config = self.config.namespaces[namespace]
            cache_key = self._get_cache_key(key, namespace)
            
            # Only cache if enabled for namespace
            if ns_config.cache_enabled:
                self._memory_cache[cache_key] = CacheEntry(
                    data,
                    ns_config.ttl_seconds
                )
            
            # Serialize and save to storage
            serialized_data = self._serialize_data(data, namespace)
            file_path = self.config.get_absolute_path(namespace) / f"{key}{self._get_file_extension(namespace)}"
            await self._fs_adapter.write_file_async(file_path, serialized_data)
            
        except Exception as e:
            self.logger.error(f"Error saving data for {namespace}:{key}: {e}")
            raise

    async def get_cached_data(self, key: str, namespace: str, model_type: Optional[Type[T]] = None) -> Optional[Any]:
        """Get data from cache or persistent storage."""
        try:
            if namespace not in self.config.namespaces:
                raise KeyError(f"Unknown namespace: {namespace}")
                
            ns_config = self.config.namespaces[namespace]
            cache_key = self._get_cache_key(key, namespace)
            
            # Try memory cache if enabled
            if ns_config.cache_enabled:
                cache_entry = self._memory_cache.get(cache_key)
                if cache_entry and not cache_entry.is_expired():
                    return cache_entry.value
            
            # Try persistent storage
            file_path = self.config.get_absolute_path(namespace) / f"{key}{self._get_file_extension(namespace)}"
            data = await self._fs_adapter.read_file_async(file_path)
            
            if data is not None:
                # Deserialize according to format
                deserialized_data = self._deserialize_data(data, namespace, model_type)
                
                # Cache if enabled
                if ns_config.cache_enabled:
                    self._memory_cache[cache_key] = CacheEntry(
                        deserialized_data,
                        ns_config.ttl_seconds
                    )
                
                return deserialized_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error loading data for {namespace}:{key}: {e}")
            return None

    async def clear_namespace_cache(self, namespace: str) -> None:
        """
        Clear all cached data for a specific namespace.
        
        Args:
            namespace: Namespace to clear
            
        Raises:
            KeyError: If namespace is unknown
        """
        if namespace not in self.config.namespaces:
            raise KeyError(f"Unknown namespace: {namespace}")
            
        self.logger.info(f"Clearing cache for namespace: {namespace}")
        
        # Clear in-memory cache for this namespace
        keys_to_remove = [
            k for k in self._memory_cache.keys() 
            if k.startswith(f"{namespace}:")
        ]
        for key in keys_to_remove:
            del self._memory_cache[key]
            
        # Clear persistent storage for this namespace if needed
        if self.config.namespaces[namespace].persistent:
            namespace_dir = self.config.get_absolute_path(namespace)
            if namespace_dir.exists():
                for file_path in namespace_dir.glob("*"):
                    if file_path.is_file():
                        try:
                            file_path.unlink()
                        except Exception as e:
                            self.logger.error(f"Failed to delete file {file_path}: {e}")
                            
        self.logger.debug(f"Cache cleared for namespace: {namespace}")

    async def save_cached_content(self, key: str, namespace: str, data: Any) -> bool:
        """Save content to cache."""
        try:
            await self.save_cached_data(key, namespace, data)
            return True
        except Exception as e:
            self.logger.error(f"Error saving content for {namespace}:{key}: {e}")
            return False

    def get_cached_content(self, key: str, namespace: str) -> Optional[Any]:
        """Get content from cache."""
        try:
            return self.get_cached_data(key, namespace)
        except Exception as e:
            self.logger.error(f"Error getting content for {namespace}:{key}: {e}")
            return None

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
        try:
            # Vérifier d'abord dans le cache
            if await self.get_cached_data(key, namespace) is not None:
                self.logger.debug(f"Content found in cache for {namespace}:{key}")
                return True
                
            # Sinon vérifier dans le stockage
            file_path = self.config.get_absolute_path(namespace) / f"{key}{self._get_file_extension(namespace)}"
            self.logger.debug(f"Looking for file at path: {file_path} (absolute: {file_path.absolute()})")
            exists = file_path.exists()
            self.logger.debug(f"File exists: {exists}")
            return exists
            
        except Exception as e:
            self.logger.error(f"Error checking content existence: {str(e)}", exc_info=True)
            return False

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
        try:
            # Vérifier d'abord dans le cache
            cached_data = await self.get_cached_data(key, namespace)
            if cached_data is not None:
                self.logger.debug(f"Content found in cache for {namespace}:{key}")
                return cached_data
                
            # Sinon charger depuis le stockage
            file_path = self.config.get_absolute_path(namespace) / f"{key}{self._get_file_extension(namespace)}"
            self.logger.debug(f"Looking for file at path: {file_path} (absolute: {file_path.absolute()})")
            self.logger.debug(f"Base path is: {self.config.base_path} (absolute: {self.config.base_path.absolute()})")
            self.logger.debug(f"File exists: {file_path.exists()}")
            
            if not file_path.exists():
                return None
                
            content = await self._fs_adapter.read_file(file_path)
            self.logger.debug(f"Content loaded: {content is not None}")
            
            if content:
                # Mettre en cache pour les prochaines fois
                await self.save_cached_data(key, namespace, content)
            return content
            
        except Exception as e:
            self.logger.error(f"Error loading raw content: {str(e)}", exc_info=True)
            return None

    async def delete_cached_content(self, key: str, namespace: str) -> bool:
        """Delete content from cache."""
        try:
            cache_key = self._get_cache_key(key, namespace)
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]
            
            file_path = self.config.get_absolute_path(namespace) / f"{key}{self._get_file_extension(namespace)}"
            await self._fs_adapter.delete_file_async(file_path)
            return True
        except Exception as e:
            self.logger.error(f"Error deleting content for {namespace}:{key}: {e}")
            return False