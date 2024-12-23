"""
Narrator Manager Protocol
Defines the interface for narrative content management.
"""
from typing import Dict, Any, Optional, Protocol, runtime_checkable, Union
from models.narrator_model import NarratorModel
from models.errors_model import NarratorError
from config.storage_config import StorageConfig
from managers.protocols.cache_manager_protocol import CacheManagerProtocol

@runtime_checkable
class NarratorManagerProtocol(Protocol):
    """Protocol for narrative content management."""
    
    def __init__(self, config: StorageConfig, cache_manager: CacheManagerProtocol) -> None:
        """Initialize narrator manager."""
        ...
        
    async def get_cached_content(self, section_number: int) -> Optional[NarratorModel]:
        """
        Get content from cache only.
        
        Args:
            section_number: Section number to get content for
            
        Returns:
            Optional[NarratorModel]: Cached content if found, None otherwise
        """
        ...
        
    async def get_raw_content(self, section_number: int) -> Union[str, NarratorError]:
        """
        Get raw content from storage.
        
        Args:
            section_number: Section number to get content for
            
        Returns:
            Union[str, NarratorError]: Raw content or error if not found
        """
        ...
        
    async def save_content(self, model: NarratorModel) -> Union[NarratorModel, NarratorError]:
        """
        Save content to cache.
        
        Args:
            model: Narrator model to save
            
        Returns:
            Union[NarratorModel, NarratorError]: Saved content or error
        """
        ...
        
    def format_content(self, content: str, section_number: int) -> Union[NarratorModel, NarratorError]:
        """
        Format content into NarratorModel.
        
        Args:
            content: Content to format
            section_number: Section number for the content
            
        Returns:
            Union[NarratorModel, NarratorError]: Formatted content or error
        """
        ...
        
    async def exists_raw_section(self, section_number: int) -> bool:
        """
        Check if raw section exists.
        
        Args:
            section_number: Section number to check
            
        Returns:
            bool: True if section exists, False otherwise
        """
        ...
        
    async def get_raw_section_content(self, section_number: int) -> Optional[str]:
        """
        Get raw section content.
        
        Args:
            section_number: Section number to get content for
            
        Returns:
            Optional[str]: Raw content if found, None otherwise
        """
        ...
        
    async def exists_section(self, section_number: int) -> bool:
        """
        Check if a section exists.
        
        Args:
            section_number: Section number to check
            
        Returns:
            bool: True if section exists, False otherwise
        """
        ...
