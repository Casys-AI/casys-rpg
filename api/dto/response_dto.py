"""Response DTOs for the API."""
from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class GameResponse(BaseModel):
    """Game response with state."""
    success: bool = True
    message: Optional[str] = None
    game_id: Optional[str] = None
    state: Dict[str, Any]


class ActionResponse(BaseModel):
    """Response to a game action."""
    success: bool = True
    message: Optional[str] = None
    action_result: Optional[Dict[str, Any]] = None
    state: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
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
