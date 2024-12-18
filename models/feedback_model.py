"""
Feedback Model Module
Contains models for handling user feedback and game state snapshots
"""

from typing import Dict, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from models.game_state import GameState
from models.trace_model import TraceModel

class FeedbackRequest(BaseModel):
    """Model for user feedback requests with game state context"""
    
    # Feedback content
    content: str = Field(
        description="The actual feedback content from the user"
    )
    feedback_type: str = Field(
        description="Type of feedback (bug, suggestion, comment, etc.)",
        default="comment"
    )
    
    # Game context
    current_section: int = Field(
        description="Section number where feedback was given"
    )
    game_state: GameState = Field(
        description="Snapshot of game state at feedback time"
    )
    trace_history: List[TraceModel] = Field(
        description="History of game decisions and events up to feedback point",
        default_factory=list
    )
    
    # Metadata
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the feedback was submitted"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="Optional identifier for the user"
    )
    session_id: str = Field(
        description="Game session identifier"
    )
    
    class Config:
        """Pydantic model configuration"""
        json_schema_extra = {
            "example": {
                "content": "Found a bug in combat calculation",
                "feedback_type": "bug",
                "current_section": 42,
                "game_state": {},  # Will be filled with GameState example
                "trace_history": [],  # Will be filled with trace examples
                "session_id": "session_123",
                "user_id": "user_456"
            }
        }
