"""
Cache Manager Module
Handles caching of game sections and related data.
"""

from typing import Dict, Optional, Any, ClassVar
from typing import TYPE_CHECKING
from datetime import datetime
import logging
import os
import json
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict

from config.component_config import ComponentConfig
from config.managers.cache_manager_config import CacheManagerConfig
from models.trace_model import TraceModel
from models.narrator_model import NarratorModel
from models.rules_model import RulesModel
from managers.protocols.cache_manager_protocol import CacheManagerProtocol

if TYPE_CHECKING:
    from models.game_state import GameState
    from models.narrator_model import NarratorModel, SourceType
    from models.rules_model import RulesModel, DiceType

import shutil

class CacheManager(ComponentConfig[CacheManagerConfig], CacheManagerProtocol):
    """
    Manages caching of game sections, rules, and trace data.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    config: CacheManagerConfig

    _section_cache: Dict[int, Any] = {}
    _current_session: Optional[Path] = None
    logger: ClassVar[logging.Logger] = logging.getLogger(__name__)
    
    def initialize(self) -> None:
        """Initialize cache directories."""
        os.makedirs(self.config.cache_dir, exist_ok=True)
        os.makedirs(self.config.content_dir, exist_ok=True)
        os.makedirs(self.config.rules_cache_dir, exist_ok=True)
        os.makedirs(self.config.trace_dir, exist_ok=True)
        
        # Initialize session directory
        self._current_session = self.create_session_dir()

    def create_session_dir(self) -> Path:
        """Create a new session directory."""
        trace_dir = Path(self.config.trace_dir)
        
        # Clean old sessions if they exist
        if trace_dir.exists():
            for old_dir in trace_dir.glob("session_*"):
                if old_dir.is_dir():
                    try:
                        shutil.rmtree(old_dir)
                    except Exception as e:
                        self.logger.warning(f"Could not delete old directory {old_dir}: {e}")
        
        # Create new session directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = trace_dir / f"session_{timestamp}"
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    async def save_trace(self, trace: TraceModel) -> None:
        """
        Save current trace state.
        
        Args:
            trace: Current trace state to save
        """
        try:
            if not self._current_session:
                self._current_session = self.create_session_dir()
            
            # Save history
            history_file = self._current_session / "history.json"
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(trace.history, f, ensure_ascii=False, indent=2)
            
            # Save stats
            stats_file = self._current_session / "adventure_stats.json"
            with open(stats_file, "w", encoding="utf-8") as f:
                json.dump(trace.stats, f, ensure_ascii=False, indent=2)
            
            # Save full trace state
            trace_file = self._current_session / "trace_state.json"
            with open(trace_file, "w", encoding="utf-8") as f:
                json.dump(trace.model_dump(), f, ensure_ascii=False, indent=2)
                
            self.logger.debug(f"Saved trace state to {self._current_session}")
            
        except Exception as e:
            self.logger.error(f"Error saving trace: {e}")

    async def load_trace(self) -> Optional[TraceModel]:
        """
        Load trace from current session.
        
        Returns:
            Optional[TraceModel]: Loaded trace state or None if not found
        """
        try:
            if not self._current_session:
                return None
            
            trace_file = self._current_session / "trace_state.json"
            if not trace_file.exists():
                return None
            
            with open(trace_file, "r", encoding="utf-8") as f:
                trace_data = json.load(f)
                return TraceModel.model_validate(trace_data)
                
        except Exception as e:
            self.logger.error(f"Error loading trace: {e}")
            return None

    async def save_stats(self, stats: Dict[str, Any]) -> None:
        """
        Save game statistics.
        
        Args:
            stats: Statistics to save
        """
        try:
            if not self._current_session:
                self._current_session = self.create_session_dir()
            
            stats_file = self._current_session / "adventure_stats.json"
            with open(stats_file, "w", encoding="utf-8") as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
                
            self.logger.debug(f"Saved stats to {stats_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving stats: {e}")

    async def load_stats(self) -> Optional[Dict[str, Any]]:
        """
        Load game statistics.
        
        Returns:
            Optional[Dict[str, Any]]: Loaded statistics or None if not found
        """
        try:
            if not self._current_session:
                return None
            
            stats_file = self._current_session / "adventure_stats.json"
            if not stats_file.exists():
                return None
            
            with open(stats_file, "r", encoding="utf-8") as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"Error loading stats: {e}")
            return None

    def get_cache_path(self, section_number: int) -> str:
        return os.path.join(self.config.cache_dir, f"{section_number}_cached.md")
    
    def get_content_path(self, section_number: int) -> str:
        return os.path.join(self.config.content_dir, f"{section_number}.md")
        
    def get_rules_cache_path(self, section_number: int) -> str:
        return os.path.join(self.config.rules_cache_dir, f"{section_number}_rules_cached.md")
    
    def get_section_cache_path(self, section_number: int) -> str:
        """Get the cache file path for a section.
        
        Args:
            section_number: Section number
            
        Returns:
            str: Path to the cache file
        """
        return os.path.join(self.config.cache_dir, f"{section_number}_cached.md")

    def save_section_to_cache(self, section_number: int, section: NarratorModel) -> None:
        """Save section content to cache.
        
        Args:
            section_number: Section number to save
            section: Section content to save
        """
        try:
            # Prepare data for serialization
            section_data = section.model_dump()
            
            # Convert datetime to string
            if "timestamp" in section_data:
                section_data["timestamp"] = section_data["timestamp"].isoformat()
            
            cache_file = self.get_section_cache_path(section_number)
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(section_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"[CacheManager] Error saving section {section_number} to cache: {str(e)}")

    def get_section_from_cache(self, section_number: int) -> Optional[NarratorModel]:
        """Get section content from cache.
        
        Args:
            section_number: Section number to get
            
        Returns:
            Optional[NarratorModel]: Cached section content if found
        """
        try:
            cache_file = self.get_section_cache_path(section_number)
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Convert string back to datetime
                if "timestamp" in data:
                    data["timestamp"] = datetime.fromisoformat(data["timestamp"])
                    
                return NarratorModel(**data)
                
            return None
            
        except Exception as e:
            self.logger.error(f"[CacheManager] Error loading section {section_number} from cache: {str(e)}")
            return None

    def exists_raw_section(self, section_number: int) -> bool:
        """Check if raw section file exists.
        
        Args:
            section_number: Section number to check
            
        Returns:
            bool: True if file exists
        """
        content_path = os.path.join(self.config.content_dir, f"{section_number}.md")
        return os.path.exists(content_path)

    def load_raw_section_content(self, section_number: int) -> Optional[str]:
        """Load raw section content from file.
        
        Args:
            section_number: Section number to load
            
        Returns:
            Optional[str]: Raw section content if found
        """
        try:
            content_path = os.path.join(self.config.content_dir, f"{section_number}.md")
            if os.path.exists(content_path):
                with open(content_path, "r", encoding="utf-8") as f:
                    return f.read()
            return None
        except Exception as e:
            self.logger.error(f"[CacheManager] Error loading section {section_number}: {str(e)}")
            return None

    def get_rules_from_cache(self, section_number: int) -> Optional[RulesModel]:
        """Récupère les règles du cache pour une section donnée."""
        try:
            cache_file = os.path.join(self.config.rules_cache_dir, f"section_{section_number}_rules.md")
            if os.path.exists(cache_file):
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Convertir le dice_type en enum
                    dice_type = data.get("dice_type", "none").upper()
                    data["dice_type"] = getattr(DiceType, dice_type, DiceType.NONE)
                    return RulesModel(**data)
            return None
        except Exception as e:
            self.logger.error(f"[CacheManager] Erreur lecture cache règles: {e}")
            return None

    def save_rules_to_cache(self, rules: RulesModel) -> None:
        """Sauvegarde les règles dans le cache."""
        try:
            if not os.path.exists(self.config.rules_cache_dir):
                os.makedirs(self.config.rules_cache_dir)
            
            cache_file = os.path.join(self.config.rules_cache_dir, f"section_{rules.section_number}_rules.md")
            
            # Convert model to dict for serialization
            rules_data = rules.model_dump()
            
            # Convert datetime to string
            if "last_update" in rules_data:
                rules_data["last_update"] = rules_data["last_update"].isoformat()
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"[CacheManager] Erreur sauvegarde règles: {e}")

    def clear_rules_cache(self) -> None:
        """Vide le cache des règles."""
        try:
            if os.path.exists(self.config.rules_cache_dir):
                for file in os.listdir(self.config.rules_cache_dir):
                    os.remove(os.path.join(self.config.rules_cache_dir, file))
            self.logger.info("[CacheManager] Cache des règles vidé")
        except Exception as e:
            self.logger.error(f"[CacheManager] Erreur nettoyage cache règles: {e}")

    def initialize_cache_dirs(self) -> None:
        """Initialise les répertoires de cache."""
        try:
            os.makedirs(self.config.cache_dir, exist_ok=True)
            os.makedirs(self.config.rules_cache_dir, exist_ok=True)
            self.logger.info("[CacheManager] Répertoires de cache initialisés")
        except Exception as e:
            self.logger.error(f"[CacheManager] Erreur initialisation répertoires cache: {e}")