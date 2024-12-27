"""
REST endpoints for utility functions.
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from loguru import logger
from api.dto.request_dto import FeedbackRequest
from utils.game_utils import roll_dice

utils_router_rest = APIRouter(prefix="/api/utils", tags=["utils"])

@utils_router_rest.post("/feedback")
async def save_feedback(feedback: FeedbackRequest) -> Dict[str, Any]:
    """
    Save user feedback.
    """
    try:
        # TODO: Implémenter la sauvegarde du feedback
        return {"status": "success", "message": "Feedback saved successfully"}
    except Exception as e:
        logger.error(f"Failed to save feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@utils_router_rest.get("/dice/{dice_type}")
async def roll_game_dice(dice_type: str) -> Dict[str, Any]:
    """
    Roll game dice.
    
    Args:
        dice_type (str): Type of dice to roll (e.g., "d20", "2d6")
    """
    try:
        result = roll_dice(dice_type)
        return {
            "dice_type": dice_type,
            "result": result,
            "status": "success"
        }
    except ValueError as e:
        logger.error(f"Invalid dice type {dice_type}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
    )
    except Exception as e:
        logger.error(f"Failed to roll dice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
