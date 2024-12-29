"""Request DTOs for the API."""
from typing import Optional, Dict, Any
from pydantic import BaseModel


class GameInitRequest(BaseModel):
    """Game initialization request.
    
    Pour l'instant on n'a besoin de rien pour initialiser,
    plus tard on ajoutera peut-être :
    - player_id: pour identifier le joueur
    - settings: pour des paramètres de jeu spécifiques
    """
    player_id: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class FeedbackRequest(BaseModel):
    """User feedback request."""
    game_id: str
    feedback_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class ActionRequest(BaseModel):
    """Player action request."""
    game_id: str
    action_type: str
    data: Dict[str, Any]


class ChoiceRequest(BaseModel):
    """Player choice request."""
    game_id: str
    choice_id: str
    choice_text: str
    metadata: Optional[Dict[str, Any]] = None


class ResponseRequest(BaseModel):
    """Player response request."""
    game_id: str
    response: str
    metadata: Optional[Dict[str, Any]] = None
