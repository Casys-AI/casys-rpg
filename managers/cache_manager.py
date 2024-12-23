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
    StorageFormat.RAW: ".raw"
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
        """Clear all cached data for a specific namespace."""
        if namespace not in self.config.namespaces:
            raise KeyError(f"Unknown namespace: {namespace}")
                
        # Clear memory cache
        prefix = f"{namespace}:"
        self._memory_cache = {
            k: v for k, v in self._memory_cache.items()
            if not k.startswith(prefix)
        }
        
        # Clear storage
        try:
            directory = self.config.get_absolute_path(namespace)
            pattern = f"*{self._get_file_extension(namespace)}"
            files = await self._fs_adapter.list_files(directory, pattern)
            for file in files:
                await self._fs_adapter.delete_file_async(file)
        except Exception as e:
            self.logger.error(f"Error clearing namespace {namespace}: {e}")
            raise

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
                return True
                
            # Sinon vérifier dans le stockage
            file_path = self.config.get_absolute_path(namespace) / f"{key}{self._get_file_extension(namespace)}"
            return file_path.exists()
        except Exception as e:
            self.logger.error(f"Error checking content existence: {str(e)}")
            return False

    def load_raw_content(self, section_number: int, namespace: str) -> Optional[str]:
        """
        Load raw content.
        
        Args:
            section_number: Section number to load
            namespace: Namespace to load from
            
        Returns:
            Optional[str]: Raw content if found
        """
        try:
            raw_path = self.config.get_absolute_path(namespace) / f"{section_number}.md"
            return self._fs_adapter.read_file(raw_path)
        except Exception as e:
            self.logger.error(f"Error loading content {section_number} from {namespace}: {e}")
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