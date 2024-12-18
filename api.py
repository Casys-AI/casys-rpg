"""
API FastAPI pour le jeu interactif
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any, List
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from models.game_state import GameState
from models.feedback_model import FeedbackRequest
from models.character_model import CharacterModel
from models.trace_model import TraceModel
from models.decision_model import DecisionModel, DiceResult

from agents.story_graph import StoryGraph
from config.game_config import GameConfig, GameFactory
from config.agent_config import AgentConfig
from utils.game_utils import roll_dice
from utils.feedback_utils import save_feedback as save_feedback_util

import logging
import os
from datetime import datetime

# Configuration
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Logging
logger = logging.getLogger(__name__)

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
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

# Gestionnaire de l'application
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    try:
        await init_components()
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise
    
    yield
    
    # Shutdown
    try:
        # Cleanup resources
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Création de l'application
app = FastAPI(
    title="Casys RPG API",
    description="API pour le jeu de rôle interactif Casys",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instances globales
agent_manager = None
manager = ConnectionManager()

# Dépendances
async def get_agent_manager():
    if agent_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent manager not initialized"
        )
    return agent_manager

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
async def init_components():
    """Initialize all game components."""
    global agent_manager
    
    try:
        # Configuration
        config = GameConfig()
        factory = GameFactory(config=config)
        
        # Initialize managers
        agent_manager = factory.agent_manager
        await agent_manager.initialize()
        
        logger.info("Components initialized successfully")
        
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        raise

# WebSocket endpoint
@app.websocket("/ws/game")
async def websocket_endpoint(
    websocket: WebSocket,
    agent_mgr = Depends(get_agent_manager)
):
    await manager.connect(websocket)
    try:
        # Send initial state
        initial_state = await agent_mgr.get_state()
        await websocket.send_json(initial_state.model_dump())
        
        # Stream state updates
        async for state in agent_mgr.stream_state():
            await websocket.send_json(state.model_dump())
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in manager.active_connections:
            manager.disconnect(websocket)

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
        save_feedback_util(feedback)
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
        log_level="info"
    )
