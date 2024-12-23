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
    """Health check response model.
    
    Attributes:
        status (str): Current health status ('ok', 'error', etc.)
        message (str): Descriptive message about the health status
        timestamp (str): ISO formatted timestamp of the check
        version (str, optional): API version
        type (str, optional): Type of health check ('api', 'author', etc.)
    """
    status: str
    message: str
    timestamp: str
    version: Optional[str] = None
    type: Optional[str] = None


@dataclass
class GameResponse:
    """Game state response."""
    game_id: str
    state: Dict[str, Any]
    message: Optional[str] = None
