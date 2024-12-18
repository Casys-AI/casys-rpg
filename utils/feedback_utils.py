"""
Utility functions for handling user feedback
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from models.feedback_model import FeedbackRequest
from models.game_state import GameState

logger = logging.getLogger(__name__)

def validate_feedback(feedback: FeedbackRequest) -> None:
    """
    Validate feedback content and structure
    
    Args:
        feedback: The FeedbackRequest object to validate
        
    Raises:
        ValueError: If feedback is invalid
    """
    if not feedback.content.strip():
        raise ValueError("Feedback content cannot be empty")
        
    if len(feedback.content) > 1000:
        raise ValueError("Feedback content must be less than 1000 characters")
    
    if not feedback.session_id:
        raise ValueError("Session ID is required")

def save_feedback(feedback: FeedbackRequest, feedback_dir: Optional[str] = None) -> None:
    """
    Save user feedback to a file with game state context
    
    Args:
        feedback: The FeedbackRequest object containing feedback and game state
        feedback_dir: Optional directory path for saving feedback. If None, uses default path.
    
    Raises:
        ValueError: If feedback validation fails
        IOError: If there's an error writing the feedback
    """
    try:
        # Validate feedback
        validate_feedback(feedback)
        
        # Use default path if none provided
        if feedback_dir is None:
            feedback_dir = Path("data/feedback")
        else:
            feedback_dir = Path(feedback_dir)
            
        # Create feedback directory if it doesn't exist
        feedback_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp and session ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"feedback_{timestamp}_{feedback.session_id}.json"
        
        # Save feedback with full context
        feedback_path = feedback_dir / filename
        with open(feedback_path, "w", encoding="utf-8") as f:
            json.dump(feedback.model_dump(), f, indent=2, default=str)
            
        logger.info(f"Saved feedback to {feedback_path}")
            
    except Exception as e:
        logger.error(f"Error saving feedback: {e}")
        raise
