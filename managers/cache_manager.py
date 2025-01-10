"""
Cache Manager Module
Handles caching and persistence of game data through a unified interface.
"""

from typing import Dict, Optional, Any, Union, Type, TypeVar, List
from datetime import datetime, timedelta
import json
from pathlib import Path
from pydantic import BaseModel
from loguru import logger

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
        self._fs_adapter = FileSystemAdapter(config)
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._current_session: Optional[Path] = None
        logger.debug("CacheManager initialized with config: {}", config.__class__.__name__)
        logger.debug("Base storage path: {}", config.base_path.absolute())

    def _get_cache_key(self, key: str, namespace: str) -> str:
        """Generate a unique cache key."""
        cache_key = f"{namespace}:{key}"
        logger.trace("Generated cache key: {}", cache_key)
        return cache_key

    def _get_file_extension(self, namespace: str) -> str:
        """Get file extension for namespace."""
        format = self.config.namespaces[namespace].format
        extension = _FORMAT_TO_EXTENSION[format]
        logger.trace("Got file extension for namespace {}: {}", namespace, extension)
        return extension

    def _serialize_data(self, data: Any, namespace: str) -> str:
        """Serialize data according to namespace format."""
        format = self.config.namespaces[namespace].format
        logger.debug("Serializing data for namespace {} with format {}", namespace, format)
        
        try:
            if format == StorageFormat.JSON:
                if isinstance(data, BaseModel):
                    logger.debug("Serializing Pydantic model to JSON, data before: {}", data)
                    data_dict = data.model_dump(exclude_none=False)
                    logger.debug("Data after model_dump: {}", data_dict)
                    serialized = json.dumps(data_dict, default=_json_serial)
                    logger.debug("Data after json.dumps: {}", serialized)
                    return serialized
                logger.trace("Serializing raw data to JSON")
                return json.dumps(data, default=_json_serial)
            elif format == StorageFormat.MARKDOWN:
                logger.trace("Serializing to Markdown format")
                if hasattr(data, 'to_markdown'):
                    logger.trace("Using custom to_markdown method")
                    return data.to_markdown()
                elif isinstance(data, BaseModel):
                    logger.trace("Converting Pydantic model to Markdown")
                    return self._model_to_markdown(data)
                else:
                    logger.trace("Converting raw data to string")
                    return str(data)
            else:  # RAW
                logger.trace("Using raw string format")
                return str(data)
        except Exception as e:
            logger.error("Error serializing data for namespace {}: {}", namespace, str(e))
            logger.error("Data type: {}", type(data))
            raise

    def _deserialize_data(self, data: str, namespace: str, model_type: Optional[Type[T]] = None) -> Any:
        """Deserialize data according to namespace format."""
        format = self.config.namespaces[namespace].format
        logger.debug("Deserializing data for namespace {} with format {}", namespace, format)
        
        try:
            if format == StorageFormat.JSON:
                logger.trace("Parsing JSON data")
                json_data = json.loads(data)
                if model_type:
                    logger.trace("Converting JSON to model type: {}", model_type.__name__)
                    return model_type.model_validate(json_data)
                return json_data
            elif format == StorageFormat.MARKDOWN:
                logger.trace("Processing Markdown data")
                if model_type and hasattr(model_type, 'from_markdown'):
                    logger.trace("Using custom from_markdown method")
                    return model_type.from_markdown(data)
                return data
            else:  # RAW
                logger.trace("Returning raw data")
                return data
        except Exception as e:
            logger.error("Error deserializing data for namespace {}: {}", namespace, str(e))
            logger.error("Raw data: {}", data[:200] + "..." if len(data) > 200 else data)
            raise

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
        logger.debug("Saving data for key {} in namespace {}", key, namespace)
        
        try:
            if namespace not in self.config.namespaces:
                logger.error("Unknown namespace: {}", namespace)
                raise KeyError(f"Unknown namespace: {namespace}")
                
            ns_config = self.config.namespaces[namespace]
            cache_key = self._get_cache_key(key, namespace)
            
            # Only cache if enabled for namespace
            if ns_config.cache_enabled:
                logger.trace("Caching in memory with TTL: {} seconds", ns_config.ttl_seconds)
                self._memory_cache[cache_key] = CacheEntry(
                    data,
                    ns_config.ttl_seconds
                )
            
            # Serialize and save to storage
            logger.debug("Serializing data for storage")
            serialized_data = self._serialize_data(data, namespace)
            file_path = self.config.get_absolute_path(namespace) / f"{key}{self._get_file_extension(namespace)}"
            logger.debug("Saving to file: {}", file_path.absolute())
            await self._fs_adapter.write_file_async(file_path, serialized_data)
            logger.info("Successfully saved data for {}/{}", namespace, key)
            
        except Exception as e:
            logger.error("Error saving data for {}/{}: {}", namespace, key, str(e))
            logger.error("Full error details:", exc_info=True)
            raise

    async def get_cached_data(self, key: str, namespace: str, model_type: Optional[Type[T]] = None) -> Optional[Any]:
        """Get data from cache or persistent storage."""
        logger.debug("Getting data for key {} in namespace {}", key, namespace)
        
        try:
            if namespace not in self.config.namespaces:
                logger.error("Unknown namespace: {}", namespace)
                raise KeyError(f"Unknown namespace: {namespace}")
                
            ns_config = self.config.namespaces[namespace]
            cache_key = self._get_cache_key(key, namespace)
            
            # Try memory cache if enabled
            if ns_config.cache_enabled:
                logger.trace("Checking memory cache")
                cache_entry = self._memory_cache.get(cache_key)
                if cache_entry:
                    if cache_entry.is_expired():
                        logger.debug("Cache entry expired")
                        del self._memory_cache[cache_key]
                    else:
                        logger.debug("Found in memory cache")
                        return cache_entry.value
            
            # Try persistent storage
            file_path = self.config.get_absolute_path(namespace) / f"{key}{self._get_file_extension(namespace)}"
            logger.debug("Looking for file: {}", file_path.absolute())
            
            data = await self._fs_adapter.read_file_async(file_path)
            
            if data is not None:
                logger.debug("Found in persistent storage")
                # Deserialize according to format
                deserialized_data = self._deserialize_data(data, namespace, model_type)
                
                # Cache if enabled
                if ns_config.cache_enabled:
                    logger.trace("Caching deserialized data")
                    self._memory_cache[cache_key] = CacheEntry(
                        deserialized_data,
                        ns_config.ttl_seconds
                    )
                
                return deserialized_data
            
            logger.debug("Data not found in cache or storage")
            return None
            
        except Exception as e:
            logger.error("Error getting data for {}/{}: {}", namespace, key, str(e))
            logger.error("Full error details:", exc_info=True)
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
            logger.error("Unknown namespace: {}", namespace)
            raise KeyError(f"Unknown namespace: {namespace}")
            
        logger.info("Clearing cache for namespace: {}", namespace)
        
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
                            logger.error("Failed to delete file {}: {}", file_path, str(e))
                            
        logger.debug("Cache cleared for namespace: {}", namespace)

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
            # Utilise load_raw_content qui gère déjà la vérification et le chargement
            content = await self.load_raw_content(key, namespace)
            return content is not None
            
        except Exception as e:
            logger.error("Error checking content existence: {}", str(e))
            logger.error("Full error details:", exc_info=True)
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
                logger.debug("Content found in cache for {}/{}", namespace, key)
                return cached_data
                
            # Sinon charger depuis le stockage
            file_path = self.config.get_absolute_path(namespace) / f"{key}{self._get_file_extension(namespace)}"
            logger.debug("Looking for file at path: {}", file_path.absolute())
            logger.debug("Base path is: {}", self.config.base_path.absolute())
            logger.debug("File exists: {}", file_path.exists())
            
            if not file_path.exists():
                return None
                
            content = await self._fs_adapter.read_file_async(file_path)
            logger.debug("Content loaded: {}", content is not None)
            
            if content:
                # Mettre en cache pour les prochaines fois
                await self.save_cached_data(key, namespace, content)
            return content
            
        except Exception as e:
            logger.error("Error loading raw content: {}", str(e))
            logger.error("Full error details:", exc_info=True)
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
            logger.error("Error deleting content for {}/{}: {}", namespace, key, str(e))
            return False

    async def update_game_id(self, game_id: str) -> None:
        """Update the game ID for per-game namespaces.
        
        Args:
            game_id: New game ID to use
        """
        logger.info("Updating game ID to: {}", game_id)
        self.config.game_id = game_id
        
        # Re-initialize filesystem adapter to create new directories
        super().__init__(self.config)
        
        # Create per-game directories
        for namespace, ns_config in self.config.namespaces.items():
            if ns_config.per_game:
                path = self.config.get_absolute_path(namespace)
                logger.debug("Creating per-game directory for {}: {}", namespace, path)
                path.mkdir(parents=True, exist_ok=True)

    async def list_keys(self, namespace: str, pattern: str) -> List[str]:
        """List all keys in a namespace matching a pattern."""
        try:
            if namespace not in self.config.namespaces:
                logger.error("Unknown namespace: {}", namespace)
                raise KeyError(f"Unknown namespace: {namespace}")
                
            # Obtenir le chemin du namespace
            ns_path = self.config.get_absolute_path(namespace)
            
            # Utiliser glob pour trouver les fichiers correspondants
            import glob
            pattern_path = str(ns_path / pattern)
            matching_files = glob.glob(pattern_path)
            
            # Extraire les noms de clés des chemins de fichiers
            keys = []
            for file_path in matching_files:
                key = Path(file_path).stem  # Nom du fichier sans extension
                keys.append(key)
                
            return keys
            
        except Exception as e:
            logger.error("Error listing keys: {}", str(e))
            raise
            
    async def clear_pattern(self, namespace: str, pattern: str) -> None:
        """Clear all cached data matching a pattern in a namespace."""
        try:
            if namespace not in self.config.namespaces:
                logger.error("Unknown namespace: {}", namespace)
                raise KeyError(f"Unknown namespace: {namespace}")
                
            # Trouver toutes les clés correspondantes
            keys = await self.list_keys(namespace, pattern)
            
            # Supprimer chaque clé
            for key in keys:
                await self.delete_cached_content(key, namespace)
                
            logger.debug("Cleared {} keys matching pattern {} in namespace {}", 
                        len(keys), pattern, namespace)
                
        except Exception as e:
            logger.error("Error clearing pattern: {}", str(e))
            raise