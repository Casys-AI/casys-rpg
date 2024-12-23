"""Protocol for narrator management."""
from typing import Optional, Union
from abc import abstractmethod
from models.narrator_model import NarratorModel
from models.errors_model import NarratorError
from typing import Protocol, Dict, Any, Optional, runtime_checkable, Union
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
from config.storage_config import StorageConfig


class NarratorManagerProtocol(Protocol):
    """Protocol defining the interface for narrator managers."""

    def __init__(self, config: StorageConfig, cache_manager: CacheManagerProtocol) -> None:
        """Initialize with configuration and cache manager."""
        ...

    @abstractmethod
    async def get_section_content(self, section_number: int) -> Optional[Union[NarratorModel, NarratorError]]:
        """Get processed section content.
        
        Args:
            section_number: Section number to retrieve
            
        Returns:
            Optional[Union[NarratorModel, NarratorError]]: Processed section or error
        """
        ...
        
    @abstractmethod
    async def save_section_content(self, content: NarratorModel) -> Optional[NarratorError]:
        """Save section content to storage.
        
        Args:
            content: Content to save
            
        Returns:
            Optional[NarratorError]: Error if any
        """
        ...
        
    @abstractmethod
    async def get_raw_section_content(self, section_number: int) -> Optional[str]:
        """Get raw section content.
        
        Args:
            section_number: Section to retrieve
            
        Returns:
            Optional[str]: Raw content if found
        """
        ...
