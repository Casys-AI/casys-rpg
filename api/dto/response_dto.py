"""Response DTOs for the API."""
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ActionResponse:
    """Response to a player action."""
    success: bool
    message: str
    state: Optional[Dict[str, Any]] = None


@dataclass
class HealthResponse:
    """Health check response."""
    status: str
    message: str
    timestamp: datetime = datetime.now()


@dataclass
class GameResponse:
    """Game state response."""
    game_id: str
    state: Dict[str, Any]
    message: Optional[str] = None
