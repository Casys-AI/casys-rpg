"""Models for the rules agent."""
from typing import List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator

class DiceType(str, Enum):
    """Type of dice roll."""
    NONE = "none"
    CHANCE = "chance"
    COMBAT = "combat"

class SourceType(str, Enum):
    """Type de source pour le contenu."""
    RAW = "raw"      # Contenu chargé depuis le fichier source
    CACHED = "cached" # Contenu chargé depuis le cache

class RulesModel(BaseModel):
    """Current rules being processed."""
    section_number: int
    dice_type: DiceType = DiceType.NONE
    needs_dice: bool = False
    conditions: List[str] = Field(default_factory=list)
    next_sections: List[int] = Field(default_factory=list)
    choices: List[str] = Field(default_factory=list)
    rules_summary: str = ""
    error: Optional[str] = None
    source: str = "default"
    source_type: SourceType = Field(default=SourceType.RAW)
    last_update: datetime = Field(default_factory=datetime.now)
    
    @field_validator('section_number')
    def validate_section_number(cls, v):
        if v < 1:
            raise ValueError("Section number must be positive")
        return v
    
    @field_validator('next_sections')
    def validate_next_sections(cls, v):
        if any(section < 1 for section in v):
            raise ValueError("Section numbers must be positive")
        return list(set(v))  # Remove duplicates
    
    @model_validator(mode='after')
    def validate_choices_sections(self):
        if len(self.choices) != len(self.next_sections):
            raise ValueError("Number of choices must match number of next sections")
        return self
