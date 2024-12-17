from typing import Dict, Optional, Any, List
from pydantic import BaseModel, ConfigDict, field_validator, computed_field
import copy

class GameState(BaseModel):
    """État du jeu pour le StateGraph."""
    section_number: int = 1
    current_section: Dict[str, Any] = {
        "number": 1,
        "content": None,
        "choices": [],
        "stats": {}
    }
    formatted_content: Optional[str] = None
    rules: Dict[str, Any] = {
        "needs_dice": False,
        "dice_type": "normal",
        "conditions": [],
        "next_sections": [],
        "rules_summary": ""
    }
    decision: Dict[str, Any] = {
        "awaiting_action": "user_input",
        "section_number": 1
    }
    stats: Dict[str, Any] = {}
    history: List[Dict[str, Any]] = []
    error: Optional[str] = None
    needs_content: bool = True
    user_response: Optional[str] = None
    dice_result: Optional[Dict[str, Any]] = None
    trace: Dict[str, Any] = {
        "stats": {
            "Caractéristiques": {
                "Habileté": 10,
                "Chance": 5,
                "Endurance": 8
            },
            "Ressources": {
                "Or": 100,
                "Gemme": 5
            },
            "Inventaire": {
                "Objets": ["Épée", "Bouclier"]
            }
        },
        "history": []
    }
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
                        "Or": 100,
                        "Gemme": 5
                    },
                    "Inventaire": {
                        "Objets": ["Épée", "Bouclier"]
                    }
                },
                "history": []
            }
        return v

    def process_response(self, response: str) -> Dict[str, Any]:
        """
        Traite la réponse de l'utilisateur.
        
        Args:
            response: La réponse de l'utilisateur
            
        Returns:
            Dict: Le nouvel état du jeu
        """
        try:
            # Créer une copie modifiable de l'état
            new_state = copy.deepcopy(self)
            
            # Mettre à jour l'état avec la réponse
            new_state.user_response = response
            
            # Sauvegarder l'état actuel dans l'historique
            if new_state.current_section and "content" in new_state.current_section:
                new_state.history.append({
                    "section": new_state.current_section.copy(),
                    "response": response,
                    "stats": new_state.stats.copy() if new_state.stats else {}
                })
            
            # Indiquer qu'on a besoin de contenu pour la prochaine section
            new_state.needs_content = True
            
            return new_state.dict()
            
        except Exception as e:
            return {"error": f"Error processing response: {str(e)}"}
