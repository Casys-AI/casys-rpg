"""
Character Manager Protocol
Defines the interface for character management.
"""
from typing import Protocol, Dict, Any, Optional, runtime_checkable
from datetime import datetime
from models.character_model import CharacterModel, CharacterStats
from pydantic import BaseModel

@runtime_checkable
class CharacterManagerProtocol(Protocol):
    """Protocol defining the interface for character management."""
    
    def __init__(self, config: BaseModel, cache_manager: Any) -> None:
        """Initialize with configuration and cache manager."""
        ...
    
    @property
    def current_character(self) -> Optional[CharacterModel]:
        """Get current character with lazy loading."""
        ...

    def get_character_stats(self) -> Optional[CharacterStats]:
        """
        Get current character stats.
        
        Returns:
            Optional[CharacterStats]: Current character stats or None if no character
        
        Raises:
            CharacterError: If there's an error retrieving stats
        """
        ...

    def save_character_stats(self, stats: Dict[str, Any]) -> None:
        """
        Save character stats.
        
        Args:
            stats: Dictionary of stats to update
            
        Raises:
            CharacterError: If stats are invalid or save fails
        """
        ...

    def _validate_stats(self, stats: Dict[str, Any]) -> None:
        """
        Validate stats before saving.
        
        Args:
            stats: Dictionary of stats to validate
            
        Raises:
            CharacterError: If stats are invalid
        """
        ...

    def save_character(self, character: CharacterModel) -> None:
        """
        Save character data to cache.
        
        Args:
            character: Character model to save
            
        Raises:
            CharacterError: If save operation fails
        """
        ...

    def load_character(self, character_id: str) -> Optional[CharacterModel]:
        """
        Load character data from cache.
        
        Args:
            character_id: ID of character to load
            
        Returns:
            Optional[CharacterModel]: Loaded character or None if not found
            
        Raises:
            CharacterError: If load operation fails
        """
        ...

    def update_character_stats(self, updates: Dict[str, Any]) -> None:
        """
        Update character stats with new values.
        
        Args:
            updates: Dictionary of stats to update
            
        Raises:
            CharacterError: If update fails or stats are invalid
        """
        ...

    def get_stats_summary(self) -> str:
        """
        Get a summary of current character stats.
        
        Returns:
            str: Formatted summary of character stats
        """
        ...

    @property
    def last_save(self) -> Optional[datetime]:
        """Get timestamp of last save operation."""
        ...
