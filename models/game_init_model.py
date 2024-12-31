"""Models for game initialization."""
from typing import Optional
from pydantic import BaseModel, Field
##################
# SHould migrate to models.game_state and use with model factory

class GameInitRequest(BaseModel):
    """Request model for game initialization."""
    game_id: str = Field(description="Unique identifier for the game")
    session_id: Optional[str] = Field(
        default=None, 
        description="Optional session ID. If not provided, a new one will be generated"
    )
    starting_section: int = Field(
        default=1,
        ge=1,
        description="Section number to start from"
    )
    character_template: Optional[str] = Field(
        default=None,
        description="Optional character template to use"
    )

class GameInitResponse(BaseModel):
    """Response model for game initialization."""
    game_id: str
    session_id: str
    state: dict  # Current game state
    message: str = "Game initialized successfully"
