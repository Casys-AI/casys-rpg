"""
Streaming endpoints for real-time updates.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from loguru import logger
from managers.agent_manager import AgentManager
from managers.dependencies import get_agent_manager

stream_router_rest = APIRouter(prefix="/api/stream", tags=["stream"])

@stream_router_rest.get("/subscribe")
async def subscribe_to_game_updates(
    agent_mgr: AgentManager = Depends(get_agent_manager)
):
    """
    Subscribe to game state updates.
    Returns a server-sent events stream.
    """
    try:
        return StreamingResponse(
            agent_mgr.stream_game_state(),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Error subscribing to updates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@stream_router_rest.post("/navigate/{section_number}")
async def navigate_to_section_with_updates(
    section_number: int,
    agent_mgr: AgentManager = Depends(get_agent_manager)
):
    """
    Navigate to a section with streaming updates.
    Returns a server-sent events stream with navigation progress.
    """
    try:
        return StreamingResponse(
            agent_mgr.navigate_to_section_with_updates(section_number),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Error streaming section {section_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
