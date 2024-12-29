"""
REST endpoints for game management.
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from managers.agent_manager import AgentManager
from managers.dependencies import get_agent_manager
from api.utils.serialization_utils import from_game_state
from api.dto.request_dto import GameInitRequest, ActionRequest
from api.dto.response_dto import GameResponse, ActionResponse
from models.game_state import GameState

game_router_rest = APIRouter(prefix="/api/game", tags=["game"])

@game_router_rest.post("/initialize")
async def initialize_game(
    agent_mgr: AgentManager = Depends(get_agent_manager)
) -> GameResponse:
    """
    Initialize a new game session.
    """
    try:
        game_state = await agent_mgr.initialize_game()
        state_dict = from_game_state(game_state)
        return GameResponse(
            game_id=state_dict.get("game_id", ""),
            state=state_dict
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
        return {"status": "success", "message": "Game stopped successfully"}
    except Exception as e:
        logger.error(f"Failed to stop game: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@game_router_rest.get("/state")
async def get_game_state(
    agent_mgr: AgentManager = Depends(get_agent_manager)
) -> GameResponse:
    """
    Get current game state.
    """
    try:
        game_state = await agent_mgr.get_state()
        if not game_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active game found"
            )
        state_dict = from_game_state(game_state)
        return GameResponse(
            game_id=state_dict.get("game_id", ""),
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

@game_router_rest.post("/action")
async def process_action(
    action: ActionRequest,
    agent_mgr: AgentManager = Depends(get_agent_manager)
) -> ActionResponse:
    """
    Process a game action.
    """
    try:
        result = await agent_mgr.process_action(action.dict())
        return ActionResponse(**result)
    except Exception as e:
        logger.error(f"Failed to process action: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@game_router_rest.post("/navigate/{section_number}")
async def navigate_to_section(
    section_number: int,
    agent_mgr: AgentManager = Depends(get_agent_manager)
) -> Dict[str, Any]:
    """
    Navigate to a specific section.
    """
    try:
        state = await agent_mgr.navigate_to_section(section_number)
        return from_game_state(state)
    except Exception as e:
        logger.error(f"Failed to navigate to section {section_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@game_router_rest.post("/response")
async def submit_response(
    response: str,
    agent_mgr: AgentManager = Depends(get_agent_manager)
) -> Dict[str, Any]:
    """
    Submit a user response.
    """
    try:
        result = await agent_mgr.process_response(response)
        return from_game_state(result)
    except Exception as e:
        logger.error(f"Failed to process response: {e}")
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
    Reset the game state and clear cookies.
    """
    try:
        # Arrêter le jeu en cours
        await agent_mgr.stop_game()
        
        # Nettoyer l'état
        if agent_mgr.managers.state_manager:
            await agent_mgr.managers.state_manager.clear_state()
            
        return {
            "status": "success",
            "message": "Game reset successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to reset game: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
