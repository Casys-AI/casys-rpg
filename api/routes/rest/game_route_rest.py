"""REST routes for game management."""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from managers.agent_manager import AgentManager
from managers.dependencies import get_agent_manager
from api.utils.serialization_utils import from_game_state

from api.dto.request_dto import GameInitRequest
from api.dto.response_dto import GameResponse

game_router_rest = APIRouter(prefix="/api/game", tags=["game"])


@game_router_rest.post("/initialize")
async def initialize_game(
    init_request: GameInitRequest,
    agent_mgr: AgentManager = Depends(get_agent_manager)
) -> GameResponse:
    """
    Initialize a new game session.
    """
    try:
        # Pour l'instant on n'utilise pas init_request
        game_state = await agent_mgr.initialize_game()
        state_dict = from_game_state(game_state)
        return GameResponse(
            success=True,
            game_id=state_dict["game_id"],
            state=state_dict,
            message="Game initialized successfully"
        )
    except Exception as e:
        logger.error(f"Failed to initialize game: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@game_router_rest.post("/stop")
async def stop_game(
    agent_mgr: AgentManager = Depends(get_agent_manager)
):
    """
    Stop the current game session and cleanup resources.
    """
    try:
        await agent_mgr.stop_game()
        return {
            "success": True,
            "message": "Game stopped successfully"
        }
    except Exception as e:
        logger.error(f"Failed to stop game: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@game_router_rest.get("/state")
async def get_game_state(
    game_id: Optional[str] = None,
    agent_mgr: AgentManager = Depends(get_agent_manager)
) -> GameResponse:
    """
    Get current game state.
    """
    try:
        if not game_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="game_id is required"
            )
        game_state = await agent_mgr.get_state()
        if not game_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game state not found"
            )
        state_dict = from_game_state(game_state)
        return GameResponse(
            game_id=state_dict["game_id"],  # game_id est toujours présent
            state=state_dict
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get game state: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@game_router_rest.get("/feedback")
async def get_feedback(
    agent_mgr: AgentManager = Depends(get_agent_manager)
) -> Dict[str, Any]:
    """
    Get feedback about current game state.
    """
    try:
        feedback = await agent_mgr.get_feedback()
        return from_game_state(feedback)
    except Exception as e:
        logger.error(f"Failed to get feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@game_router_rest.post("/reset")
async def reset_game(
    agent_mgr: AgentManager = Depends(get_agent_manager)
):
    """
    Reset the game state and clear all data.
    """
    try:
        # Arrêter le jeu en cours
        await agent_mgr.stop_game()
        
        # Nettoyer l'état
        if agent_mgr.managers.state_manager:
            await agent_mgr.managers.state_manager.clear_state()
            
        return {
            "success": True,
            "message": "Game reset successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to reset game: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
