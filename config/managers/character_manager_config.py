"""Character Manager configuration."""
from typing import Dict, Any, List
from pydantic import Field

from config.managers.manager_config_base import ManagerConfigBase

class CharacterManagerConfig(ManagerConfigBase):
    """Configuration for the Character Manager."""
    
    # Character attributes
    base_attributes: List[str] = Field(
        default=["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"],
        description="Base character attributes"
    )
    
    # Stats management
    auto_save: bool = Field(
        default=True,
        description="Automatically save character stats"
    )
    save_interval: int = Field(
        default=300,
        description="Auto-save interval in seconds"
    )
    
    # Validation
    validate_stats: bool = Field(
        default=True,
        description="Validate stat changes"
    )
    allow_negative: bool = Field(
        default=False,
        description="Allow negative stat values"
    )
