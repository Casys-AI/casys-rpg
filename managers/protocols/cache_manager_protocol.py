"""
Cache Manager Protocol
Defines the interface for cache management in the game engine.
"""
from typing import Protocol, Dict, Optional, Any, runtime_checkable
from pathlib import Path
from models.trace_model import TraceModel
from models.narrator_model import NarratorModel
from models.rules_model import RulesModel

@runtime_checkable
class CacheManagerProtocol(Protocol):
    """Protocol defining the interface for cache management."""
    
    def initialize(self) -> None:
        """Initialize cache directories."""
        ...

    def create_session_dir(self) -> Path:
        """Create a new session directory."""
        ...

    def save_trace(self, trace: TraceModel) -> None:
        """Save current trace state."""
        ...

    def load_trace(self) -> Optional[TraceModel]:
        """Load trace from current session."""
        ...

    def save_stats(self, stats: Dict[str, Any]) -> None:
        """Save game statistics."""
        ...

    def load_stats(self) -> Optional[Dict[str, Any]]:
        """Load game statistics."""
        ...

    def save_section_to_cache(self, section_number: int, section: NarratorModel) -> None:
        """Save section content to cache."""
        ...

    def get_section_from_cache(self, section_number: int) -> Optional[NarratorModel]:
        """Get section content from cache."""
        ...

    def exists_raw_section(self, section_number: int) -> bool:
        """Check if raw section file exists."""
        ...

    def load_raw_section_content(self, section_number: int) -> Optional[str]:
        """Load raw section content from file."""
        ...

    def get_rules_from_cache(self, section_number: int) -> Optional[RulesModel]:
        """Get rules from cache for a given section."""
        ...

    def save_rules_to_cache(self, rules: RulesModel) -> None:
        """Save rules to cache."""
        ...

    def clear_rules_cache(self) -> None:
        """Clear rules cache."""
        ...
