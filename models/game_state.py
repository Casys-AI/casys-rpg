"""Models for game state management."""
from typing import Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict

from models.decision_model import DiceResult, DecisionModel
from models.character_model import CharacterModel
from models.narrator_model import NarratorModel, SourceType as NarratorSourceType
from models.rules_model import RulesModel, DiceType, SourceType as RulesSourceType
from models.trace_model import TraceModel

class GameStateInput(BaseModel):
    """Input state for the game workflow."""
    section_number: int
    player_input: Optional[str] = None
    effects: Dict[str, Any] = Field(default_factory=dict)
    flags: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        },
        arbitrary_types_allowed=True
    )

class GameStateOutput(BaseModel):
    """Output state from the game workflow."""
    narrative: Optional[NarratorModel] = None
    rules: Optional[RulesModel] = None
    trace: Optional[TraceModel] = None
    character: Optional[CharacterModel] = None
    dice_roll: Optional[DiceResult] = None
    decision: Optional[DecisionModel] = None
    error: Optional[str] = None
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        },
        arbitrary_types_allowed=True
    )

class GameState(GameStateInput, GameStateOutput):
    """Complete game state at a point in time."""
    source: RulesSourceType = RulesSourceType.RAW
    narrative_content: Optional[str] = None
    current_rules: Optional[Dict[str, Any]] = None
    current_decision: Optional[Dict[str, Any]] = None
    last_update: datetime = Field(
        default_factory=datetime.now,
        json_schema_extra={"format": "date-time"}
    )
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        },
        arbitrary_types_allowed=True
    )
    
    @model_validator(mode='before')
    def handle_addable_values(cls, values):
        """Handle AddableValuesDict and ensure all required fields are present."""
        if str(type(values)) == "<class 'langgraph.pregel.io.AddableValuesDict'>" and 'error' in values:
            error_msg = values.get('error', '')
            if '{section_number}' in error_msg:
                error_msg = error_msg.format(section_number=1)
            
            values = {
                'section_number': 1,
                'error': error_msg,
                'player_input': None,
                'effects': {},
                'flags': {},
                'source': RulesSourceType.RAW,
                'last_update': datetime.now()
            }
        return values

    @field_validator('section_number')
    def validate_section_number(cls, v):
        """Validate section number is positive."""
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
            
        return self

    def with_updates(self, **updates) -> "GameState":
        """Create a new state with updates."""
        state_dict = self.model_dump()
        state_dict.update(updates)
        return GameState(**state_dict)
        
    def model_dump_json(self, **kwargs):
        """Override model_dump_json to handle datetime serialization."""
        return super().model_dump_json(
            **{k: v for k, v in kwargs.items() if k != 'default'}
        )

    @classmethod
    def create_initial_state(cls) -> "GameState":
        """Create an initial game state with all models initialized."""
        return cls(
            section_number=1,
            narrative=NarratorModel(
                section_number=1,
                content="",
                source_type=NarratorSourceType.RAW
            ),
            rules=RulesModel(
                section_number=1,
                dice_type=DiceType.NONE,
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

    @classmethod
    def create_from_section(cls, section_number: int) -> 'GameState':
        """Create game state for a specific section.
        
        Args:
            section_number: Section number to create state for
            
        Returns:
            GameState: New game state instance
            
        Raises:
            ValueError: If section number is invalid
        """
        return cls(
            section_number=section_number,
            source=RulesSourceType.RAW,
            player_input=None,
            effects={},
            flags={}
        )
        
    @classmethod
    def create_error_state(cls, error_message: str, section_number: int = 1, current_state: Optional["GameState"] = None) -> "GameState":
        """Create a game state with error, optionally preserving current state.
        
        Args:
            error_message: Error message to include
            section_number: Section number to use if no current state
            current_state: Optional current state to preserve
            
        Returns:
            GameState: New game state with error
        """
        if current_state:
            state_dict = current_state.model_dump()
            state_dict.update({
                "section_number": current_state.section_number,
                "error": error_message
            })
            return cls(**state_dict)
        
        # Pour un nouvel état, initialiser tous les champs obligatoires
        return cls(
            section_number=section_number,
            source=RulesSourceType.RAW,
            error=error_message,
            player_input=None,
            effects={},
            flags={},
            narrative=None,
            rules=None,
            trace=None,
            character=None,
            dice_roll=None,
            decision=None,
            narrative_content=None,
            current_rules=None,
            current_decision=None
        )
