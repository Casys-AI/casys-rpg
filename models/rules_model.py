"""Models for the rules agent."""
from typing import List, Optional, Dict, Union, Literal, Annotated
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from models.types.common_types import NextActionType

class DiceType(str, Enum):
    """Type of dice roll."""
    NONE = "none"
    CHANCE = "chance"
    COMBAT = "combat"

class SourceType(str, Enum):
    """Type de source pour le contenu."""
    RAW = "raw"      # Contenu chargé depuis le fichier source
    PROCESSED = "processed" # Contenu chargé depuis le cache
    ERROR = "error"  # État d'erreur

class ChoiceType(str, Enum):
    """Type of choice available."""
    DIRECT = "direct"        # Direct choice to a section
    CONDITIONAL = "conditional"  # Choice depends on conditions
    DICE = "dice"           # Choice depends on dice roll
    MIXED = "mixed"         # Combination of conditions and dice

class Choice(BaseModel):
    """Represents a choice in the game."""
    text: str = Field(description="The text of the choice presented to the player")
    type: ChoiceType = Field(description="The type of choice (direct, conditional, dice, mixed)")
    target_section: Optional[int] = Field(None, description="The section number this choice leads to")
    conditions: List[str] = Field(default_factory=list, description="List of conditions that must be met")
    dice_type: Optional[DiceType] = Field(None, description="Type of dice roll required")
    dice_results: Dict[str, int] = Field(
        default_factory=dict,
        description="Mapping of dice roll results to target sections"
    )
    
    @field_validator('dice_type')
    def validate_dice_type(cls, v: Optional[DiceType]) -> Optional[DiceType]:
        """Convert dice_type to lowercase and validate."""
        if isinstance(v, str):
            return DiceType(v.lower())
        return v
    
    @model_validator(mode='after')
    def validate_choice_type(self) -> 'Choice':
        """Validate that the choice has the correct fields for its type."""
        if self.type == ChoiceType.DIRECT:
            if self.target_section is None:
                raise ValueError("Direct choices must have a target section")
            if self.dice_type not in (None, DiceType.NONE):
                raise ValueError("Direct choices cannot have dice rolls")
            if self.conditions:
                raise ValueError("Direct choices cannot have conditions")
                
        elif self.type == ChoiceType.CONDITIONAL:
            if not self.conditions:
                raise ValueError("Conditional choices must have conditions")
            if self.dice_type not in (None, DiceType.NONE):
                raise ValueError("Conditional choices cannot have dice rolls")
                
        elif self.type == ChoiceType.DICE:
            if self.dice_type in (None, DiceType.NONE):
                raise ValueError("Dice choices must specify dice type")
            if not self.dice_results:
                raise ValueError("Dice choices must have dice results")
            if self.conditions:
                raise ValueError("Dice choices cannot have conditions")
                
        elif self.type == ChoiceType.MIXED:
            if not self.conditions:
                raise ValueError("Mixed choices must have conditions")
            if self.dice_type in (None, DiceType.NONE):
                raise ValueError("Mixed choices must specify dice type")
            if not self.dice_results:
                raise ValueError("Mixed choices must have dice results")
                
        return self

class RulesModel(BaseModel):
    """Current rules being processed."""
    
    section_number: Annotated[int, Field(..., gt=0, description="Current section number")]
    dice_type: DiceType = Field(default=DiceType.NONE, description="Type of dice roll needed")
    needs_dice: bool = Field(default=False, description="Indicates if a dice roll is needed")
    needs_user_response: bool = Field(
        default=False,
        description="Indicates if a user response is needed"
    )
    next_action: Optional[NextActionType] = Field(
        default=None,
        description="Order of actions ('user_first' or 'dice_first')"
    )
    conditions: List[str] = Field(
        default_factory=list,
        description="List of conditions that apply to this section"
    )
    choices: List[Choice] = Field(
        default_factory=list,
        description="List of available choices in this section"
    )
    rules_summary: str = Field(
        default="",
        description="Summary of the rules for this section"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if any"
    )
    source: str = Field(
        default="default",
        description="Source of the rules content"
    )
    source_type: SourceType = Field(
        default=SourceType.RAW,
        description="Type of source for the content"
    )
    last_update: datetime = Field(default_factory=datetime.now, description="Date de mise à jour spécifique aux règles")

    @model_validator(mode='after')
    def validate_rules(self) -> 'RulesModel':
        """Validate the rules model for consistency."""
        # Vérifier si on a des choix qui nécessitent des dés
        has_dice_choice = any(
            choice.type in (ChoiceType.DICE, ChoiceType.MIXED)
            for choice in self.choices
        )
        
        # Si on a des choix avec dés, on doit avoir needs_dice et un dice_type
        if has_dice_choice:
            self.needs_dice = True
            if self.dice_type == DiceType.NONE:
                # Prendre le type de dé du premier choix qui en a un
                self.dice_type = next(
                    (choice.dice_type for choice in self.choices if choice.dice_type),
                    DiceType.CHANCE  # Default to chance if no specific type
                )
        
        # Si dice_type est none, needs_dice doit être false
        if self.dice_type == DiceType.NONE:
            self.needs_dice = False
        
        # Si on a besoin de dés, on doit avoir un type de dé non-none
        if self.needs_dice and self.dice_type == DiceType.NONE:
            raise ValueError("needs_dice cannot be True when dice_type is none")
            
        # Si on a des choix, on a besoin d'une réponse utilisateur
        if self.choices:
            self.needs_user_response = True
            
        # Vérifier la cohérence de next_action
        if self.next_action:
            if not self.needs_dice and not self.needs_user_response:
                raise ValueError("next_action can only be set if needs_dice or needs_user_response is True")
            if self.next_action == "dice_first" and not self.needs_dice:
                raise ValueError("next_action cannot be dice_first when needs_dice is False")
            if self.next_action == "user_first" and not self.needs_user_response:
                raise ValueError("next_action cannot be user_first when needs_user_response is False")
            
        return self

    @model_validator(mode='after')
    def validate_rules(self) -> 'RulesModel':
        """Validate the rules model for consistency."""
        # Validate dice_type based on needs_dice
        if self.needs_dice and self.dice_type == DiceType.NONE:
            raise ValueError("Dice type must be specified when dice roll is needed")
        if not self.needs_dice and self.dice_type != DiceType.NONE:
            self.dice_type = DiceType.NONE  # Reset dice type if no dice needed
            
        # Validate error state
        if self.error and self.source_type != SourceType.ERROR:
            self.source_type = SourceType.ERROR
            
        return self

    class Config:
        """Configuration for the model."""
        json_schema_extra = {
            "example": {
                "dice_type": "none",
                "needs_dice": False,
                "needs_user_response": True,
                "next_action": "user_first",
                "conditions": ["has_sword", "health > 0"],
                "choices": [
                    {
                        "text": "Go to the castle",
                        "type": "direct",
                        "target_section": 2
                    }
                ],
                "rules_summary": "Player must have a sword and health above 0 to proceed"
            }
        }
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
