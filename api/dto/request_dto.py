"""Request DTOs for the API."""
from typing import Optional, Dict, Any
from pydantic import BaseModel


class GameInitRequest(BaseModel):
    """Game initialization request."""
    game_id: str
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
