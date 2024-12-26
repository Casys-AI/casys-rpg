"""Models for game state management."""
from typing import Dict, Optional, Any, Annotated
from datetime import datetime
from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict, validator
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

def take_last_value(a: Any, b: Any) -> Any:
    """Take the last value for LangGraph fan-in."""
    return b

class GameStateBase(BaseModel):
    """Base state model with common fields."""
    session_id: Annotated[str, first_not_none]  # Le session_id doit être fourni explicitement
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        },
        arbitrary_types_allowed=True,
        use_enum_values=True  # Utiliser les valeurs des enums plutôt que les noms
    )   

class GameStateInput(GameStateBase):
    """Input state for the game workflow."""
    section_number: Annotated[int, take_last_value] = Field(default=1)  # Premier cycle par défaut
    player_input: Optional[str] = None
    content: Optional[str] = None

    @field_validator('section_number')
    def validate_section_number(cls, v):
        """Validate section number."""
        if v < 1:
            raise ValueError("Section number must be positive")
        return v

class GameStateOutput(GameStateBase):
    """Output state from the game workflow."""
    # Content models
    narrative: Annotated[Optional[NarratorModel], take_last_value] = None
    rules: Annotated[Optional[RulesModel], take_last_value] = None
    
    # Game state
    trace: Optional[TraceModel] = None
    character: Optional[CharacterModel] = None
    decision: Optional[DecisionModel] = None
    
    # Global error state
    error: Annotated[Optional[str], first_not_none] = None  # Erreurs générales du workflow
    
    @field_validator('error', mode='before')
    @classmethod
    def validate_error(cls, v):
        if isinstance(v, list):
            return next((x for x in v if x is not None), None)
        return v
    
    @field_validator('narrative', 'rules', mode='before')
    @classmethod
    def validate_models(cls, v):
        if isinstance(v, list):
            # Prendre le dernier modèle de la liste
            return v[-1] if v else None
        return v

    @model_validator(mode='after')
    def sync_section_numbers(self) -> 'GameStateOutput':
        """Synchronize and validate section numbers between models."""
        if self.narrative and self.rules:
            if self.narrative.section_number != self.rules.section_number:
                raise ValueError(
                    f"Section numbers must match between narrative ({self.narrative.section_number}) "
                    f"and rules ({self.rules.section_number})"
                )
        return self

class GameState(GameStateInput, GameStateOutput):
    """Complete game state at a point in time."""
    
    def __add__(self, other: 'GameState') -> 'GameState':
        """Merge two GameStates for LangGraph parallel results.
        Takes the latest state while preserving session_id from the first state.
        
        Note: Unlike NarratorModel and RulesModel, GameState allows different section numbers
        and will take the section number from the latest state.
        
        Args:
            other: Another GameState to merge with
            
        Returns:
            A new GameState with the latest state and original session_id
        """
        if not isinstance(other, GameState):
            return self
            
        # Créer une copie du nouvel état
        new_state = other.model_copy()
        # Garder le session_id original
        new_state.session_id = self.session_id
        return new_state
        
    @field_validator('section_number', mode='before')
    @classmethod
    def validate_section_number(cls, v):
        if isinstance(v, list):
            # Vérifier que tous les numéros sont identiques
            if len(set(v)) > 1:
                raise ValueError(f"Inconsistent section numbers in list: {v}")
            # Prendre le dernier numéro de section
            return v[-1] if v else 0
        return v

    @property
    def state(self) -> Dict[str, Any]:
        """
        Get the complete state as a dictionary.
        
        Uses model_dump with configuration for proper serialization:
        - exclude_none: Remove None fields to reduce payload size
        - by_alias: Use field aliases for consistent naming
        - exclude_unset: Remove fields that weren't explicitly set
        
        Returns:
            Dict[str, Any]: Serialized state with all necessary fields
        """
        return self.model_dump(
            exclude_none=True,     # Exclure les champs None
            by_alias=True,         # Utiliser les alias pour la sérialisation
            exclude_unset=True,    # Exclure les champs non définis
            exclude={              # Exclure les champs internes spécifiques
                'session_id': False,  # Toujours inclure session_id
                'error': False       # Toujours inclure error même si None
            }
        )

    @model_validator(mode='after')
    def validate_state(self) -> 'GameState':
        """Validate the complete state."""
        if self.error and not isinstance(self.error, str):
            self.error = str(self.error)
        return self

    @model_validator(mode='before')
    def sync_section_numbers(cls, values: Dict[str, Any]) -> Dict[str, Any]:  # pylint: disable=no-self-argument
        """Synchronize section numbers between models."""
        if 'section_number' in values:
            section_number = values['section_number']
            # Si c'est un nombre, on le prend tel quel
            if isinstance(section_number, int):
                target_section = section_number
            # Si c'est une liste (résultat de l'addition), on prend le dernier
            elif isinstance(section_number, list):
                # Vérifier que tous les numéros sont identiques
                if len(set(section_number)) > 1:
                    raise ValueError(f"Inconsistent section numbers in list: {section_number}")
                target_section = section_number[-1] if section_number else 0
            else:
                return values
                
            if 'narrative' in values and values['narrative']:
                if isinstance(values['narrative'], list):
                    # Prendre le dernier modèle
                    values['narrative'] = values['narrative'][-1]
                if hasattr(values['narrative'], 'model_dump'):
                    narrative_data = values['narrative'].model_dump()
                    narrative_data['section_number'] = target_section
                    values['narrative'] = narrative_data

            if 'rules' in values and values['rules']:
                if isinstance(values['rules'], list):
                    # Prendre le dernier modèle
                    values['rules'] = values['rules'][-1]
                if hasattr(values['rules'], 'model_dump'):
                    rules_data = values['rules'].model_dump()
                    rules_data['section_number'] = target_section
                    values['rules'] = rules_data
        return values
        
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
            session_id=self.session_id,
            section_number=self.section_number,
            player_input=self.player_input,
            content=self.content
        )
        
    def to_output(self) -> GameStateOutput:
        """Convert to output state."""
        return GameStateOutput(
            session_id=self.session_id,
            narrative=self.narrative,
            rules=self.rules,
            trace=self.trace,
            character=self.character,
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
    def create_error_state(cls, error_message: str, session_id: str, section_number: int = 1, current_state: Optional["GameState"] = None) -> "GameState":
        """Create a game state with error, optionally preserving current state.
        
        Args:
            error_message: Error message to include
            session_id: Session ID for the error state
            section_number: Section number to use if no current state
            current_state: Optional current state to preserve
            
        Returns:
            GameState: New game state with error
        """
        if current_state:
            state_dict = current_state.model_dump()
            state_dict.update({
                "section_number": current_state.section_number,
                "error": error_message,
                "session_id": session_id
            })
            return cls(**state_dict)
        
        # Pour un nouvel état, initialiser tous les champs obligatoires
        return cls(
            session_id=session_id,
            section_number=section_number,
            source=RulesSourceType.RAW,
            error=error_message,
            player_input=None,
            content=None,
            narrative=None,
            rules=None,
            trace=None,
            character=None,
            decision=None
        )
