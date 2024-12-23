"""Models for the trace agent."""
from typing import Dict, List, Optional, Any, Annotated
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

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
    model_config = ConfigDict(frozen=True)  # Immutable model for better safety

    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the action occurred"
    )
    section: Annotated[int, Field(gt=0, description="Section number must be positive")]
    action_type: ActionType = Field(description="Type of action performed")
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional details about the action"
    )

    @model_validator(mode='after')
    def validate_action_details(self) -> 'TraceAction':
        """Validate that the details are consistent with the action type.
        
        Returns:
            TraceAction: The validated action
            
        Raises:
            ValueError: If the details are invalid for the action type
        """
        if self.action_type == ActionType.DICE_ROLL and 'roll_result' not in self.details:
            raise ValueError("Dice roll actions must include 'roll_result' in details")
        if self.action_type == ActionType.USER_INPUT and 'input' not in self.details:
            raise ValueError("User input actions must include 'input' in details")
        return self

class TraceModel(BaseModel):
    """Current state of the game trace."""
    model_config = ConfigDict(validate_assignment=True)  # Validate on attribute assignment

    game_id: str = Field(description="Unique game identifier")
    session_id: Annotated[str, Field(min_length=1, description="Unique session identifier")]
    section_number: Annotated[int, Field(ge=0, description="Current section number")] = 0
    start_time: datetime = Field(
        default_factory=datetime.now,
        description="When this trace was started"
    )
    history: List[TraceAction] = Field(
        default_factory=list,
        description="History of all actions in this session"
    )
    current_section: Optional[NarratorModel] = None
    current_rules: Optional[RulesModel] = None
    character: Optional[CharacterModel] = None
    error: Optional[str] = None

    @model_validator(mode='after')
    def validate_model_consistency(self) -> 'TraceModel':
        """Validate that the model state is consistent.
        
        Returns:
            TraceModel: The validated model
            
        Raises:
            ValueError: If the model state is inconsistent
        """
        if self.error and (self.current_section or self.current_rules):
            raise ValueError("Error state cannot have current section or rules")
        if bool(self.current_section) != bool(self.current_rules):
            raise ValueError("Current section and rules must both be set or both be None")
        return self

    def add_action(self, action: Dict[str, Any]):
        """Add a new action to the trace history.

        Args:
            action (Dict[str, Any]): A dictionary containing action details with the following structure:
                - section (int): The section number where the action occurred
                - action_type (ActionType): The type of action (user_input, dice_roll, etc.)
                - details (Dict[str, Any]): Additional details about the action

        Example:
            ```python
            trace.add_action({
                'section': 1,
                'action_type': ActionType.DICE_ROLL,
                'details': {'roll_result': 6}
            })
            ```
        """
        action['timestamp'] = datetime.now()
        self.history.append(TraceAction(**action))

    def update_character(self, character: CharacterModel):
        """Update the character state in the trace model.

        Args:
            character (CharacterModel): The new character state to update with.
                This will replace the current character state in the trace.
        """
        self.character = character
        self.add_action({
            "section": self.section_number,
            "action_type": ActionType.CHARACTER_UPDATE,
            "details": {"character": character.model_dump()}
        })
