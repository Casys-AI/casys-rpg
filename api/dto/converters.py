"""Converters between DTOs and domain models."""
from typing import Dict, Any
from datetime import datetime

from models.game_state import GameState
from models.feedback_model import FeedbackRequest as DomainFeedbackRequest

from .request_dto import GameInitRequest, FeedbackRequest, ActionRequest
from .response_dto import ActionResponse, GameResponse


def to_game_state(data: Dict[str, Any]) -> GameState:
    """Convert API data to GameState model."""
    return GameState(**data)


def from_game_state(state: GameState) -> Dict[str, Any]:
    """
    Convert GameState model to API response data.
    
    Uses model_dump() for proper serialization of all fields,
    including nested Pydantic models.
    
    Args:
        state: GameState instance to convert
        
    Returns:
        Dict containing the serialized state
    """
    return state.model_dump(
        exclude_none=True,    # Exclure les champs None
        by_alias=True,        # Utiliser les alias pour la sérialisation
        exclude_unset=True    # Exclure les champs non définis
    )


def to_domain_feedback(request: FeedbackRequest) -> DomainFeedbackRequest:
    """Convert FeedbackRequest DTO to domain FeedbackRequest."""
    return DomainFeedbackRequest(
        content=request.content,
        feedback_type=request.feedback_type,
        current_section=0,  # À définir selon le contexte
        game_state=GameState(),  # À définir selon le contexte
        session_id=request.game_id,
        metadata=request.metadata or {}
    )
