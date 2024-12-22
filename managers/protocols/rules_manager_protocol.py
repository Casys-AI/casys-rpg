"""
Rules Manager Protocol
Defines the interface for rules management.
"""
from typing import Protocol, Dict, Any, Optional, runtime_checkable, Union
from config.storage_config import StorageConfig
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
from models.rules_model import RulesModel
from models.errors_model import RulesError

@runtime_checkable
class RulesManagerProtocol(Protocol):
    """Protocol defining the interface for rules management."""
    
    def __init__(self, config: StorageConfig, cache_manager: CacheManagerProtocol) -> None:
        """Initialize with configuration and cache manager."""
        ...
        
    async def get_existing_rules(self, section_number: int) -> Union[RulesModel, RulesError]:
        """
        Get existing rules for a section from storage.
        
        Args:
            section_number: Section number to get rules for
            
        Returns:
            Union[RulesModel, RulesError]: Rules if found, or error if not found
        """
        ...
        
    async def save_rules(self, rules: RulesModel) -> Union[RulesModel, RulesError]:
        """
        Save rules to storage.
        
        Args:
            rules: Rules to save
            
        Returns:
            Union[RulesModel, RulesError]: Saved rules or error
        """
        ...
        
    async def exists_raw_rules(self, section_number: int) -> bool:
        """
        Check if rules exist for a section.
        
        Args:
            section_number: Section number to check
            
        Returns:
            bool: True if rules exist
        """
        ...
        
    def get_rules_content(self, section_number: int) -> Optional[str]:
        """
        Get raw rules content for a section.
        
        Args:
            section_number: Section number to get content for
            
        Returns:
            Optional[str]: Raw rules content if found
        """
        ...
