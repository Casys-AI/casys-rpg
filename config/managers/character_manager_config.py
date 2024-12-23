"""Character Manager configuration."""
from typing import List
from pydantic import Field
from config.storage_config import StorageConfig

class CharacterManagerConfig(StorageConfig):
    """Configuration for the Character Manager."""
    
    # Character attributes
    base_attributes: List[str] = Field(
        default=["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"],
        description="Base character attributes"
    )
    