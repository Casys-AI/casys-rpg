"""
Rules Manager Protocol
Defines the interface for game rules management.
"""
from typing import Dict, Any, List, Optional, Protocol, runtime_checkable, Union
from models.rules_model import RulesModel
from models.errors_model import RulesError
from config.storage_config import StorageConfig
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
from models.game_state import GameState  # Added import for GameState

@runtime_checkable
class RulesManagerProtocol(Protocol):
    """Protocol for rules management operations."""
    
    def __init__(self, config: StorageConfig, cache_manager: CacheManagerProtocol) -> None:
        """Initialize rules manager."""
        ...
        
    async def get_cached_rules(self, section_number: int) -> Optional[RulesModel]:
        """
        Get rules from cache only.
        
        Args:
            section_number: Section number to get rules for
            
        Returns:
            Optional[RulesModel]: Cached rules if found, None otherwise
        """
        ...
        
    async def get_raw_content(self, section_number: int) -> Union[str, RulesError]:
        """
        Get raw content from storage.
        
        Args:
            section_number: Section number to get content for
            
        Returns:
            Union[str, RulesError]: Raw content or error if not found
        """
        ...
        
    async def save_rules(self, rules: RulesModel) -> Union[RulesModel, RulesError]:
        """
        Save rules to cache.
        
        Args:
            rules: Rules model to save
            
        Returns:
            Union[RulesModel, RulesError]: Saved rules or error
        """
        ...
        
    def _rules_to_markdown(self, rules: RulesModel) -> str:
        """
        Convert rules to markdown format.
        
        Args:
            rules: Rules model to convert
            
        Returns:
            str: Markdown formatted rules
        """
        ...
        
    def _markdown_to_rules(self, content: str, section_number: int) -> Optional[RulesModel]:
        """
        Convert markdown content to RulesModel.
        
        Args:
            content: Markdown content to convert
            section_number: Section number
            
        Returns:
            Optional[RulesModel]: Converted model or None if failed
        """
        ...