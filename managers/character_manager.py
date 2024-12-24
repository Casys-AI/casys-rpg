"""
Character Manager Module
Handles character stats and progression.
"""
from typing import Dict, Optional, Any
from datetime import datetime
import logging
from pathlib import Path

from config.storage_config import StorageConfig
from models.character_model import CharacterModel, CharacterStats
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
from managers.protocols.character_manager_protocol import CharacterManagerProtocol
from models.errors_model import CharacterError

class CharacterManager(CharacterManagerProtocol):
    """Manages character stats and progression."""
    
    def __init__(self, config: StorageConfig, cache_manager: CacheManagerProtocol):
        """Initialize CharacterManager with configuration."""
        self.config = config
        self.cache = cache_manager
        self.logger = logging.getLogger(__name__)
        self._current_character: Optional[CharacterModel] = None

    @property
    def current_character(self) -> Optional[CharacterModel]:
        """Get current character with lazy loading."""
        if not self._current_character:
            self._current_character = self.load_character("current")
        return self._current_character

    def get_character_stats(self) -> Optional[CharacterStats]:
        """Get current character stats."""
        try:
            return self.current_character.stats if self.current_character else None
        except Exception as e:
            self.logger.error(f"Error getting character stats: {e}")
            raise CharacterError(f"Failed to get character stats: {str(e)}")

    def save_character_stats(self, stats: Dict[str, Any]) -> None:
        """Save character stats."""
        try:
            if not self.current_character:
                self._current_character = CharacterModel()
            
            # Validate stats
            self._validate_stats(stats)
            
            self.current_character.stats.update(stats)
            self.save_character(self.current_character)
            
        except Exception as e:
            self.logger.error(f"Error saving character stats: {e}")
            raise CharacterError(f"Failed to save character stats: {str(e)}")

    def load_character(self, character_id: str) -> Optional[CharacterModel]:
        """Load character from storage."""
        try:
            character_data = self.cache.get_cached_data(
                key=character_id,
                namespace="characters"
            )
            
            if not character_data:
                return None
                
            return CharacterModel.model_validate(character_data)
            
        except Exception as e:
            self.logger.error(f"Error loading character: {e}")
            raise CharacterError(f"Failed to load character: {str(e)}")

    def save_character(self, character: CharacterModel) -> None:
        """Save character data to cache."""
        try:
            self.cache.save_cached_data(
                key=str(character.id),
                namespace="characters",
                data=character.model_dump()
            )
        except Exception as e:
            self.logger.error(f"Error saving character: {e}")
            raise CharacterError(f"Failed to save character: {str(e)}")

    def update_character_stats(self, stats_update: Dict[str, Any]) -> None:
        """Update character stats."""
        try:
            if not self.current_character:
                self._current_character = CharacterModel()
            
            # Validate stats update
            self._validate_stats(stats_update)
            
            # Update stats
            self.current_character.stats.update(stats_update)
            self.save_character(self.current_character)
            
        except Exception as e:
            self.logger.error(f"Error updating character stats: {e}")
            raise CharacterError(f"Failed to update character stats: {str(e)}")

    def _validate_stats(self, stats: Dict[str, Any]) -> None:
        """Validate character stats."""
        try:
            for key, value in stats.items():
                if not isinstance(value, (int, float)):
                    raise CharacterError(f"Invalid stat value for {key}: must be numeric")
                if value < 0:
                    raise CharacterError(f"Invalid stat value for {key}: cannot be negative")
        except Exception as e:
            raise CharacterError(f"Stats validation failed: {str(e)}")

    def get_stats_summary(self) -> str:
        """Get a summary of current character stats."""
        try:
            if not self.current_character or not self.current_character.stats:
                return "No character stats available"
                
            stats = self.current_character.stats
            return (
                f"Level {stats.level} Character\n"
                f"HP: {stats.health}/{stats.max_health}\n"
                f"STR: {stats.strength} | DEX: {stats.dexterity} | INT: {stats.intelligence}\n"
                f"XP: {stats.experience}"
            )
            
        except Exception as e:
            self.logger.error(f"Error getting stats summary: {e}")
            return "Error retrieving character stats"
