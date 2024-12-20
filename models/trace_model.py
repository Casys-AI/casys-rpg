"""Models for the trace agent."""
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator

from models.character_model import CharacterModel
from models.narrator_model import NarratorModel
from models.rules_model import RulesModel

class ActionType(str, Enum):
    """Types d'actions possibles dans le jeu."""
    USER_INPUT = "user_input"
    DICE_ROLL = "dice_roll"
    SECTION_CHANGE = "section_change"
    CHARACTER_UPDATE = "character_update"
    ERROR = "error"

class TraceAction(BaseModel):
    """A single action in the game trace."""
    timestamp: datetime = Field(default_factory=datetime.now)
    section: int
    action_type: ActionType
    details: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('section')
    def validate_section(cls, v):
        if v < 1:
            raise ValueError("Section must be positive")
        return v
    
    @field_validator('action_type')
    def validate_action_type(cls, v):
        if not v.strip():
            raise ValueError("Action type cannot be empty")
        return v

class TraceModel(BaseModel):
    """Current state of the game trace."""
    section_number: int = 0
    history: List[TraceAction] = Field(default_factory=list)
    current_section: Optional[NarratorModel] = None
    current_rules: Optional[RulesModel] = None
    character: Optional[CharacterModel] = None
    error: Optional[str] = None
    
    @field_validator('section_number')
    def validate_section_number(cls, v):
        if v < 0:
            raise ValueError("Section number cannot be negative")
        return v
    
    def add_action(self, action: Dict[str, Any]):
        """Add an action to the trace history."""
        if not isinstance(action, TraceAction):
            action = TraceAction(**action)
        self.history.append(action)
    
    def update_character(self, character: CharacterModel):
        """Update character state in trace."""
        self.character = character
        self.add_action({
            "section": self.section_number,
            "action_type": ActionType.CHARACTER_UPDATE,
            "details": {"character": character.model_dump()}
        })
