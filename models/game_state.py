"""Models for game state management."""
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field, model_validator, field_validator

from models.decision_model import DiceResult, DecisionModel
from models.character_model import CharacterModel
from models.narrator_model import NarratorModel, SourceType as NarratorSourceType
from models.rules_model import RulesModel, SourceType as RulesSourceType
from models.trace_model import TraceModel

class GameState(BaseModel):
    """Complete game state at a point in time."""
    section_number: int
    narrative: Optional[NarratorModel] = None
    rules: Optional[RulesModel] = None
    trace: Optional[TraceModel] = None
    character: Optional[CharacterModel] = None
    dice_roll: Optional[DiceResult] = None
    decision: Optional[DecisionModel] = None
    player_input: Optional[str] = None
    effects: Dict[str, Any] = Field(default_factory=dict)
    flags: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    source: RulesSourceType = RulesSourceType.RAW
    
    @field_validator('section_number')
    def validate_section_number(cls, v):
        if v < 1:
            raise ValueError("Section number must be positive")
        return v
    
    @model_validator(mode='after')
    def validate_state_consistency(self):
        """Validate that all section numbers match."""
        section = self.section_number
        
        if self.narrative and self.narrative.section_number != section:
            raise ValueError("Narrative section number mismatch")
            
        if self.rules and self.rules.section_number != section:
            raise ValueError("Rules section number mismatch")
            
        if self.trace and self.trace.section_number != section:
            raise ValueError("Trace section number mismatch")
            
        if self.decision and self.decision.section_number != section:
            raise ValueError("Decision section number mismatch")
            
        return self

    @classmethod
    def create_initial_state(cls) -> "GameState":
        """Create an initial game state."""
        return cls(
            section_number=1,
            narrative=NarratorModel(
                section_number=1,
                content="",
                source_type=NarratorSourceType.RAW
            ),
            rules=RulesModel(
                section_number=1,
                dice_type=RulesModel.DiceType.NONE,
                needs_dice=False,
                conditions=[],
                next_sections=[],
                choices=[]
            ),
            trace=TraceModel(
                section_number=1,
                actions=[],
                decisions=[]
            )
        )
