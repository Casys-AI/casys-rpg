from typing import Dict, Optional, Any, List
from pydantic import BaseModel, ConfigDict, Field, field_validator, computed_field
import copy

class GameState(BaseModel):
    """Modèle Pydantic pour l'état du jeu."""
    section_number: int = Field(default=1, description="Numéro de la section actuelle")
    current_section: Dict[str, Any] = Field(
        default_factory=lambda: {
            "number": 1,
            "content": "",  # Contenu formaté de la section
            "choices": [],
            "stats": {}
        },
        description="Section actuelle avec son contenu formaté et ses choix"
    )
    rules: Dict[str, Any] = Field(
        default_factory=lambda: {
            "needs_dice": False,
            "dice_type": "normal",
            "conditions": [],
            "next_sections": [],
            "rules_summary": ""
        },
        description="Règles de la section actuelle"
    )
    decision: Dict[str, Any] = Field(
        default_factory=lambda: {
            "awaiting_action": "user_input",
            "section_number": 1
        },
        description="État de la décision en cours"
    )
    stats: Dict[str, Any] = Field(
        default_factory=dict,
        description="Statistiques du personnage"
    )
    history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Historique des actions"
    )
    error: Optional[str] = Field(
        default=None,
        description="Message d'erreur éventuel"
    )
    needs_content: bool = Field(
        default=True,
        description="Indique si la section a besoin de contenu"
    )
    user_response: Optional[str] = Field(
        default=None,
        description="Réponse de l'utilisateur"
    )
    dice_result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Résultat du lancer de dés"
    )
    trace: Dict[str, Any] = Field(
        default_factory=lambda: {
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
        },
        description="Trace du jeu pour le suivi"
    )
    debug: bool = Field(
        default=False,
        description="Mode debug activé ou non"
    )

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
