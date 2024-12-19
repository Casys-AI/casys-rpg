"""
Character Manager Module
Manages character attributes and game statistics.
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime
import json
import logging
from pathlib import Path
from pydantic import ConfigDict

from config.component_config import ComponentConfig
from config.managers.character_manager_config import CharacterManagerConfig

class CharacterManager(ComponentConfig[CharacterManagerConfig]):
    """Manages character attributes and game statistics."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    config: CharacterManagerConfig
    _current_stats: Dict[str, Any] = {}

    def initialize(self) -> None:
        """
        Initialize character manager with static configuration.
        This is called once at startup.
        """
        self.logger = logging.getLogger(__name__)
        self._current_stats = {}
        self.cache_manager = self.config.cache_manager

    async def start_session(self) -> None:
        """
        Start a new character session.
        This loads or creates fresh character stats.
        Can be called multiple times to start new sessions.
        """
        # Reset current stats
        self._current_stats = {}
        
        # Load stats from cache if they exist
        if self.cache_manager:
            loaded_stats = self.load_stats()
            if loaded_stats:
                self._current_stats = loaded_stats

    def update_stats(self, stats: Dict[str, Any]) -> None:
        """
        Update character attributes and game statistics.
        This includes health, inventory, resources, etc.
        
        Args:
            stats: New statistics to update (e.g. {"health": 100, "gold": 50})
        """
        try:
            # Update in-memory stats
            self._current_stats.update(stats)
            
            # Persist stats to file via cache manager
            if self.cache_manager:
                self.save_stats(stats)
                
            self.logger.debug(f"Updated character stats: {list(stats.keys())}")
            
        except Exception as e:
            self.logger.error(f"Error updating character stats: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current character attributes and statistics.
        
        Returns:
            Dict[str, Any]: Current stats (e.g. {"health": 100, "gold": 50})
        """
        try:
            # Load from cache if no stats in memory
            if not self._current_stats and self.cache_manager:
                loaded_stats = self.load_stats()
                if loaded_stats:
                    self._current_stats = loaded_stats
                    
            return self._current_stats.copy()
            
        except Exception as e:
            self.logger.error(f"Error getting character stats: {e}")
            return {}

    def save_stats(self, stats: Dict[str, Any]) -> None:
        """
        Save character statistics to file.
        This creates a persistent record of the character's current state.
        
        Args:
            stats: Statistics to save
        """
        try:
            if self.cache_manager:
                session_dir = self.cache_manager.get_current_session()
                if not session_dir:
                    session_dir = self.cache_manager.create_session_dir()
                
                stats_file = session_dir / "character_stats.json"
                with open(stats_file, "w", encoding="utf-8") as f:
                    json.dump(stats, f, ensure_ascii=False, indent=2)
                    
                self.logger.debug(f"Saved character stats to {stats_file}")
                
        except Exception as e:
            self.logger.error(f"Error saving character stats: {e}")

    def load_stats(self) -> Optional[Dict[str, Any]]:
        """
        Load character statistics from file.
        This restores the character's state from a previous session.
        
        Returns:
            Optional[Dict[str, Any]]: Loaded statistics or None if not found
        """
        try:
            if self.cache_manager:
                session_dir = self.cache_manager.get_current_session()
                if not session_dir:
                    return None
                
                stats_file = session_dir / "character_stats.json"
                if not stats_file.exists():
                    return None
                
                with open(stats_file, "r", encoding="utf-8") as f:
                    return json.load(f)
                    
            return None
                
        except Exception as e:
            self.logger.error(f"Error loading character stats: {e}")
            return None
