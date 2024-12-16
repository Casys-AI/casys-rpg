from typing import Dict, Optional, Any, List
from pydantic import BaseModel, ConfigDict, field_validator

class GameState(BaseModel):
    """État du jeu pour le StateGraph."""
    section_number: int = 1
    current_section: Optional[Dict] = None
    formatted_content: Optional[str] = None
    rules: Dict = {
        "needs_dice": False,
        "dice_type": "normal",
        "conditions": [],
        "next_sections": [],
        "rules_summary": ""
    }
    decision: Dict = {
        "awaiting_action": "user_input",
        "section_number": 1
    }
    stats: Optional[Dict] = None
    history: Optional[list] = None
    error: Optional[str] = None
    needs_content: bool = True
    user_response: Optional[str] = None
    dice_result: Optional[Dict] = None
    trace: Optional[Dict] = None
    debug: bool = False

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator('rules', mode='before')
    def validate_rules(cls, v):
        if v is None:
            return {
                "needs_dice": False,
                "dice_type": "normal",
                "conditions": [],
                "next_sections": [],
                "rules_summary": ""
            }
        return v

    @field_validator('decision', mode='before')
    def validate_decision(cls, v):
        if v is None:
            return {
                "awaiting_action": "user_input",
                "section_number": 1
            }
        return v

    @field_validator('current_section', mode='before')
    def validate_current_section(cls, v):
        if v is None:
            return {
                "number": 1,
                "content": None,
                "choices": [],
                "stats": {}
            }
        return v

    @field_validator('trace', mode='before')
    def validate_trace(cls, v):
        if v is None:
            return {
                "stats": {
                    "Caractéristiques": {
                        "Habileté": 10,
                        "Chance": 5,
                        "Endurance": 8
                    },
                    "Ressources": {
                        "Or": 100
                    },
                    "Inventaire": {
                        "Objets": ["Épée", "Bouclier"]
                    }
                }
            }
        return v
