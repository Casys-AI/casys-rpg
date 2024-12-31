"""Models for decision making."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
from models.types.common_types import NextActionType
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

    class Config:
        """Configuration for the model."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AnalysisResult(BaseModel):
    """Result of decision analysis."""
    next_section: int
    conditions: List[str] = Field(default_factory=list)
    analysis: str = ""
    error: Optional[str] = None
    
    @field_validator('next_section')
    def validate_next_section(cls, v):
        if v < 1:
            raise ValueError("Next section must be positive")
        return v

    class Config:
        """Configuration for the model."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class DecisionModel(BaseModel):
    """A decision made in the game."""
    section_number: int
    next_section: Optional[int] = None
    error: Optional[str] = None
    awaiting_action: ActionType = ActionType.USER_INPUT
    conditions: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    next_action: Optional[NextActionType] = Field(
        default=None,
        description="Order of actions ('user_first' or 'dice_first')"
    )
    
    @field_validator('section_number')
    def validate_section_number(cls, v):
        if v < 1:
            raise ValueError("Section number must be positive")
        return v
        
    @field_validator('next_section')
    def validate_next_section(cls, v):
        if v is not None and v < 1:
            raise ValueError("Next section must be positive")
        return v
    
    @model_validator(mode='after')
    def validate_conditions(self):
        # Remove any duplicate conditions
        self.conditions = list(dict.fromkeys(self.conditions))
        return self

    class Config:
        """Configuration for the model."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
