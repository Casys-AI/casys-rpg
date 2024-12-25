"""Models for game state management."""
from typing import Dict, Optional, Any, Annotated
from datetime import datetime
from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict
import uuid
import operator
from typing import Annotated

from models.character_model import CharacterModel
from models.decision_model import DecisionModel
from models.narrator_model import NarratorModel
from models.rules_model import RulesModel, DiceType, SourceType as RulesSourceType
from models.trace_model import TraceModel

def first_not_none(a: Optional[str], b: Optional[str]) -> Optional[str]:
    """Return the first non-None value."""
    return a if a is not None else b

class GameStateBase(BaseModel):
    """Base state model with common fields."""
    session_id: Annotated[str, first_not_none]  # Le session_id doit être fourni explicitement
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        },
        arbitrary_types_allowed=True
    )   

class GameStateInput(GameStateBase):
    """Input state for the game workflow."""
    section_number: Annotated[int, operator.add] = Field(default=1, ge=1, description="Current section number")
    player_input: Optional[str] = None
    content: Optional[str] = None

class GameStateOutput(GameStateBase):
    """Output state from the game workflow."""
    narrative: Annotated[Optional[NarratorModel], operator.add] = None
    rules: Annotated[Optional[RulesModel], operator.add] = None
    trace: Optional[TraceModel] = None
    character: Optional[CharacterModel] = None
    dice_roll: Optional[DecisionModel] = None
    decision: Optional[DecisionModel] = None
    error: Annotated[Optional[str], first_not_none] = None
    narrative_content: Optional[str] = None
    current_rules: Optional[Dict[str, Any]] = None
    current_decision: Optional[Dict[str, Any]] = None
    source: Optional[RulesSourceType] = RulesSourceType.RAW  # Déplacé ici car utilisé principalement pour l'input

class GameState(GameStateInput, GameStateOutput):
    """Complete game state at a point in time."""
    
    @property
    def state(self) -> Dict[str, Any]:
        """Get the complete state as a dictionary with explicit 'state' key."""
        state_dict = self.model_dump()
        return state_dict

    
    @model_validator(mode='after')
    def validate_state(self) -> 'GameState':
        """Validate the complete state."""
        if self.error and not isinstance(self.error, str):
            self.error = str(self.error)
        return self

    @model_validator(mode='after')
    def validate_section_numbers(self) -> 'GameState':
        """Validate that section numbers match across components."""
        if self.narrative and self.narrative.section_number != self.section_number:
            raise ValueError(
                f"Narrative section number {self.narrative.section_number} "
                f"does not match game state section number {self.section_number}"
            )
        
        if self.rules and self.rules.section_number != self.section_number:
            raise ValueError(
                f"Rules section number {self.rules.section_number} "
                f"does not match game state section number {self.section_number}"
            )
        
        return self
        
    def update_from_input(self, input_state: GameStateInput) -> None:
        """Update state from input."""
        for field in input_state.model_fields:
            if hasattr(input_state, field):
                setattr(self, field, getattr(input_state, field))
                
    def update_from_output(self, output_state: GameStateOutput) -> None:
        """Update state from output."""
        for field in output_state.model_fields:
            if hasattr(output_state, field):
                setattr(self, field, getattr(output_state, field))
                
    def to_input(self) -> GameStateInput:
        """Convert to input state."""
        return GameStateInput(
            section_number=self.section_number,
            player_input=self.player_input,
            content=self.content
        )
        
    def to_output(self) -> GameStateOutput:
        """Convert to output state."""
        return GameStateOutput(
            narrative=self.narrative,
            rules=self.rules,
            trace=self.trace,
            character=self.character,
            dice_roll=self.dice_roll,
            decision=self.decision,
            error=self.error
        )

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
            content=None
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
            content=None,
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
