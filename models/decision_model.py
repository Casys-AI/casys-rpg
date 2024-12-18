"""Models for the decision agent."""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator

from models.rules_model import DiceType
from models.trace_model import ActionType

class DiceResult(BaseModel):
    """Result of a dice roll."""
    value: Optional[int] = None
    type: DiceType
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @field_validator('value')
    def validate_dice_value(cls, v):
        if v is not None and (v < 1 or v > 6):
            raise ValueError("Dice value must be between 1 and 6")
        return v

class DecisionModel(BaseModel):
    """A decision made in the game."""
    section_number: int
    awaiting_action: ActionType = ActionType.USER_INPUT
    conditions: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @field_validator('section_number')
    def validate_section_number(cls, v):
        if v < 1:
            raise ValueError("Section number must be positive")
        return v
    
    @model_validator(mode='after')
    def validate_conditions(self):
        # Remove any duplicate conditions
        self.conditions = list(dict.fromkeys(self.conditions))
        return self
