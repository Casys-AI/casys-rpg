"""Request DTOs for the API."""
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class GameInitRequest:
    """Game initialization request."""
    game_id: str
    player_id: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


@dataclass
class FeedbackRequest:
    """User feedback request."""
    game_id: str
    feedback_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ActionRequest:
    """Player action request."""
    game_id: str
    action_type: str
    data: Dict[str, Any]
