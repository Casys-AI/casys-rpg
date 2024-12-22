"""
API FastAPI pour le jeu interactif
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any, List
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from datetime import datetime
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.models import OpenAPI
from pathlib import Path

from models.game_state import GameState
from models.feedback_model import FeedbackRequest
from models.character_model import CharacterModel
from models.trace_model import TraceModel
from models.decision_model import DecisionModel, DiceResult

from config.game_config import GameConfig
from config.storage_config import StorageConfig, StorageFormat, NamespaceConfig
from managers.agent_manager import AgentManager
from utils.game_utils import roll_dice
from config.logging_config import get_logger

logger = get_logger('api')

# Configuration
API_HOST = "127.0.0.1"
API_PORT = 8000
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

# Classes de réponse
class ActionResponse(BaseModel):
    """Réponse à une action du joueur"""
    success: bool
    message: str
    state: GameState | None = None

class HealthResponse(BaseModel):
    """Réponse du health check"""
    status: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)

# Gestionnaire de connexions WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                self.disconnect(connection)

manager = ConnectionManager()

# Configuration globale
def get_storage_config() -> StorageConfig:
    """Get storage configuration."""
    return StorageConfig.get_default_config(BASE_DIR / "data")

# Gestionnaire de l'application
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan."""
    # Startup
    logger.info("Starting up...")
    await startup_event()
    yield
    # Shutdown
    logger.info("Shutting down...")

# Création de l'application
app = FastAPI(
    title="Casys RPG API",
    description="API pour le jeu de rôle interactif Casys",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instance unique de l'AgentManager
_agent_manager: AgentManager | None = None

def get_agent_manager() -> AgentManager:
    """Get or create AgentManager instance."""
    global _agent_manager
    if not _agent_manager:
        from agents.factories.game_factory import GameFactory
        factory = GameFactory(
            game_config=GameConfig(),
            storage_config=StorageConfig(base_path=BASE_DIR / "data")
        )
        _agent_manager = factory.agent_manager
    return _agent_manager

# Dépendances
async def get_current_state(
    agent_mgr = Depends(get_agent_manager)
) -> GameState:
    try:
        return await agent_mgr.get_state()
    except Exception as e:
        logger.error(f"Error getting game state: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Initialisation
async def startup_event():
    """Initialize components on startup."""
    try:
        agent_mgr = get_agent_manager()
        await agent_mgr.initialize_game()
        logger.info("Game components initialized")
    except Exception as e:
        logger.error(f"Failed to initialize game: {e}")
        raise

# Documentation configuration
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
        swagger_favicon_url="/static/favicon.png",
        init_oauth=None,
        swagger_ui_parameters={
            "websocket": True,  # Enable WebSocket support
            "syntaxHighlight": True,
            "tryItOutEnabled": True
        }
    )

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    agent_mgr = Depends(get_agent_manager)
):
    """
    WebSocket endpoint for real-time game state updates.
    
    The WebSocket connection will stream game state updates in the following format:
    ```json
    {
        "type": "state_update",
        "data": {
            "section_number": 1,
            "narrative": {...},
            "rules": {...},
            "decision": {...},
            "trace": {...}
        }
    }
    """
    try:
        await manager.connect(websocket)
        async for state in agent_mgr.subscribe_to_updates():
            await manager.broadcast({
                "type": "state_update",
                "data": state.model_dump()
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in manager.active_connections:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)

# Routes REST
@app.post("/game/action", response_model=ActionResponse)
async def process_action(
    action: Dict[str, Any],
    agent_mgr = Depends(get_agent_manager)
):
    try:
        state = await agent_mgr.process_action(action)
        return ActionResponse(
            success=True,
            message="Action processed successfully",
            state=state
        )
    except Exception as e:
        logger.error(f"Error processing action: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/feedback")
async def save_feedback(feedback: FeedbackRequest):
    try:
        # save_feedback_util(feedback)
        return {"status": "success", "message": "Feedback saved successfully"}
    except Exception as e:
        logger.error(f"Error saving feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    try:
        return HealthResponse(
            status="healthy",
            message="Service is running normally"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            message=str(e)
        )

@app.get("/game/roll/{dice_type}")
async def roll_game_dice(dice_type: str):
    try:
        result = roll_dice(dice_type)
        return {"result": result}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error rolling dice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/game/state", response_model=ActionResponse)
async def get_game_state(agent_mgr = Depends(get_agent_manager)) -> ActionResponse:
    """Get current game state."""
    try:
        state = await agent_mgr.get_state()
        return ActionResponse(
            success=True,
            message="State retrieved successfully",
            state=state
        )
    except Exception as e:
        logger.error(f"Error getting game state: {e}")
        return ActionResponse(
            success=False,
            message=str(e),
            state=None
        )

@app.get("/game/updates")
async def subscribe_to_game_updates(agent_mgr = Depends(get_agent_manager)):
    """Subscribe to game state updates."""
    try:
        return await agent_mgr.subscribe_to_updates()
    except Exception as e:
        logger.error(f"Error streaming updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/game/section/{section_number}", response_model=ActionResponse)
async def navigate_to_section(
    section_number: int,
    agent_mgr = Depends(get_agent_manager)
) -> ActionResponse:
    """Navigate to a specific section."""
    try:
        state = await agent_mgr.navigate_to_section(section_number)
        return ActionResponse(
            success=True,
            message=f"Navigated to section {section_number}",
            state=state
        )
    except Exception as e:
        logger.error(f"Error navigating to section {section_number}: {e}")
        return ActionResponse(
            success=False,
            message=str(e),
            state=None
        )

@app.post("/game/section/{section_number}/stream")
async def navigate_to_section_with_updates(
    section_number: int,
    agent_mgr = Depends(get_agent_manager)
):
    """Navigate to a section with streaming updates."""
    try:
        return StreamingResponse(
            agent_mgr.process_section_with_updates(section_number),
            media_type="application/x-ndjson"
        )
    except Exception as e:
        logger.error(f"Error streaming section updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/game/response", response_model=ActionResponse)
async def submit_response(
    response: str,
    agent_mgr = Depends(get_agent_manager)
) -> ActionResponse:
    """Submit a user response."""
    try:
        state = await agent_mgr.submit_response(response)
        return ActionResponse(
            success=True,
            message="Response processed successfully",
            state=state
        )
    except Exception as e:
        logger.error(f"Error processing response: {e}")
        return ActionResponse(
            success=False,
            message=str(e),
            state=None
        )

@app.post("/game/action", response_model=ActionResponse)
async def perform_action(
    action: Dict[str, Any],
    agent_mgr = Depends(get_agent_manager)
) -> ActionResponse:
    """Perform a game action."""
    try:
        state = await agent_mgr.perform_action(action)
        return ActionResponse(
            success=True,
            message="Action processed successfully",
            state=state
        )
    except Exception as e:
        logger.error(f"Error performing action: {e}")
        return ActionResponse(
            success=False,
            message=str(e),
            state=None
        )

@app.get("/game/feedback")
async def get_feedback(agent_mgr = Depends(get_agent_manager)) -> str:
    """Get feedback about current game state."""
    try:
        return await agent_mgr.get_user_feedback()
    except Exception as e:
        logger.error(f"Error getting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Exception handler global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception handler caught: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "type": type(exc).__name__
        }
    )

if __name__ == "__main__":
    logger.info(f"Starting API server on {API_HOST}:{API_PORT}")
    import uvicorn
    uvicorn.run(
        "api:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level="debug"
    )
