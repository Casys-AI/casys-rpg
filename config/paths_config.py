"""Path configuration module."""
from pathlib import Path
from typing import Dict
from pydantic import BaseModel, Field

class PathsConfig(BaseModel):
    """Configuration for all file paths used in the game."""
    
    # Base directories
    root_dir: Path = Field(
        default=Path(__file__).parent.parent,
        description="Root directory of the project"
    )
    data_dir: Path = Field(
        default=None,
        description="Directory for game data"
    )
    config_dir: Path = Field(
        default=None,
        description="Directory for configuration files"
    )
    cache_dir: Path = Field(
        default=None,
        description="Directory for cache files"
    )
    
    # Game content paths
    sections_dir: Path = Field(
        default=None,
        description="Directory for game sections"
    )
    rules_dir: Path = Field(
        default=None,
        description="Directory for game rules"
    )
    assets_dir: Path = Field(
        default=None,
        description="Directory for game assets"
    )
    
    def __init__(self, **data):
        """Initialize path configuration with default values."""
        super().__init__(**data)
        self._init_paths()
        
    def _init_paths(self) -> None:
        """Initialize derived paths from root directory."""
        # Set up main directories
        self.data_dir = self.root_dir / "data"
        self.config_dir = self.root_dir / "config"
        self.cache_dir = self.data_dir / "cache"
        
        # Set up content directories
        self.sections_dir = self.data_dir / "sections"
        self.rules_dir = self.data_dir / "rules"
        self.assets_dir = self.data_dir / "assets"
        
    def get_cache_path(self, cache_type: str) -> Path:
        """Get cache directory for specific type."""
        return self.cache_dir / cache_type
    
    def get_section_path(self, section_id: int) -> Path:
        """Get path for a specific game section."""
        return self.sections_dir / f"section_{section_id}.md"
    
    def get_rule_path(self, section_id: int) -> Path:
        """Get path for rules of a specific section."""
        return self.rules_dir / f"section_{section_id}_rules.md"
