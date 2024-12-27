"""
API FastAPI pour le jeu interactif
"""

# Standard library imports
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, AsyncGenerator
import sys
import logging
from contextlib import asynccontextmanager
from datetime import datetime
import json

# Third-party imports
from fastapi import FastAPI, WebSocket, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from starlette.websockets import WebSocketDisconnect, WebSocketState

# Local imports
from config.storage_config import StorageConfig
from config.game_config import GameConfig
from config.logging_config import get_logger

from models.game_state import GameState
from models.errors_model import GameError, NarratorError, StateError, AgentError
from models.decision_model import DiceResult, DecisionModel
from models.character_model import CharacterModel
from models.trace_model import TraceModel

from managers.agent_manager import AgentManager

from agents.factories.game_factory import GameFactory, GameAgents, GameManagers

from api.socketio import init_socketio
from api.dto.request_dto import GameInitRequest, FeedbackRequest, ActionRequest
from api.dto.response_dto import ActionResponse, GameResponse, HealthResponse
from api.dto.converters import to_game_state, from_game_state, to_domain_feedback

from utils.game_utils import roll_dice

# Initialize logger
logger = get_logger('api')

# Configuration
API_HOST = os.getenv("CASYS_HOST", "127.0.0.1")
API_PORT = int(os.getenv("CASYS_PORT", "8001"))  # Changed default port to 8001
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

# Add project root to PYTHONPATH
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

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

# Composants du jeu
_game_factory: GameFactory | None = None
_agent_manager: AgentManager | None = None
_game_components: tuple[GameAgents, GameManagers] | None = None

def get_agent_manager() -> AgentManager:
    """Get AgentManager instance."""
    global _agent_manager, _game_factory, _game_components
    
    if not _agent_manager:
        logger.info("Creating new AgentManager instance")
        if not _game_factory:
            logger.debug("Creating new GameFactory instance")
            _game_factory = GameFactory()
        
        if not _game_components:
            logger.debug("Creating game components")
            _game_components = _game_factory.create_game_components()
            
        agents, managers = _game_components
        logger.debug("Initializing AgentManager with components")
        _agent_manager = AgentManager(
            agents=agents,
            managers=managers,
            game_factory=_game_factory,
            story_graph_config=_game_factory._config.agent_configs.story_graph_config
        )
        logger.info("AgentManager initialized successfully")
    else:
        logger.debug("Returning existing AgentManager instance")
        
    return _agent_manager

# Gestionnaire de l'application
async def shutdown_event():
    """Cleanup API components."""
    try:
        global _game_factory, _agent_manager, _game_components
        
        # Cleanup agent manager
        if _agent_manager:
            logger.debug("Cleaning up AgentManager")
            await _agent_manager.stop_game()
        
        # Reset global variables
        _game_factory = None
        _agent_manager = None
        _game_components = None
        
        logger.info("API shutdown successfully")
    except Exception as e:
        logger.error(f"Failed to shutdown API: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan."""
    # Startup
    logger.info("Starting up...")
    await startup_event()
    yield
    # Shutdown
    logger.info("Shutting down...")
    await shutdown_event()

# Configuration CORS
origins = [
    "http://localhost:9000",  # Frontend Qwik
    "http://127.0.0.1:9000",
    "http://localhost:8001",  # API
    "http://127.0.0.1:8001",
    "http://localhost:5173",  # Frontend Qwik (dev)
    "ws://localhost:8001",    # WebSocket
    "ws://localhost:5173",    # WebSocket (dev)
    "http://127.0.0.1:5173", # Frontend Qwik (dev)
    "ws://127.0.0.1:5173",   # WebSocket (dev)
]

# Création de l'application
app = FastAPI(
    title="Casys RPG API",
    description="API pour le jeu de rôle interactif Casys",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None
)

# Configuration des middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Socket.IO
socket_manager = init_socketio(app)

# Dépendances
async def get_current_state(
    agent_mgr = Depends(get_agent_manager)
) -> GameState:
    """Get current game state."""
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
    """Initialize API components."""
    try:
        global _game_factory, _agent_manager, _game_components
        
        # Initialize game factory
        logger.debug("Initializing GameFactory")
        _game_factory = GameFactory()
        
        # Create game components
        logger.debug("Creating game components")
        _game_components = _game_factory.create_game_components()
        
        # Initialize agent manager
        agents, managers = _game_components
        logger.debug("Initializing AgentManager")
        _agent_manager = AgentManager(
            agents=agents,
            managers=managers,
            game_factory=_game_factory,
            story_graph_config=_game_factory._config.agent_configs.story_graph_config
        )
        
        logger.info("API started successfully")
    except Exception as e:
        logger.error(f"Failed to start API: {e}")
        raise

# Documentation configuration
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    """Custom Swagger UI HTML."""
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html>
        <head>
            <link type="text/css" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
            <title>Casys RPG API - Documentation</title>
            <style>
                body {
                    margin: 0;
                }
                .swagger-ui .info {
                    margin: 20px;
                }
            </style>
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
            <script>
                window.onload = () => {
                    window.ui = SwaggerUIBundle({
                        url: '/openapi.json',
                        dom_id: '#swagger-ui',
                        deepLinking: true,
                        presets: [
                            SwaggerUIBundle.presets.apis,
                            SwaggerUIBundle.SwaggerUIStandalonePreset
                        ],
                        plugins: [
                            SwaggerUIBundle.plugins.DownloadUrl
                        ],
                        layout: "BaseLayout"
                    });
                };
            </script>
        </body>
        </html>
        """
    )

def custom_openapi():
    """Custom OpenAPI schema configuration."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Casys RPG API",
        version="1.0.0",
        description="""API pour le jeu de rôle interactif Casys.
        
        ## Fonctionnalités
        
        - Gestion des sessions de jeu
        - Communication en temps réel via WebSocket
        - Système de dés contextuel
        - Gestion de l'état du jeu
        - Historique des actions
        
        ## Architecture
        
        L'API utilise une architecture événementielle avec :
        - FastAPI pour l'API REST
        - Socket.IO pour la communication temps réel
        - LangGraph pour l'orchestration des agents
        """,
        routes=app.routes,
    )
    
    # Personnalisation des tags
    openapi_schema["tags"] = [
        {
            "name": "Game",
            "description": "Opérations de jeu (actions, navigation, dés)"
        },
        {
            "name": "WebSocket",
            "description": "Communication en temps réel (état du jeu, mises à jour)"
        },
        {
            "name": "System",
            "description": "Opérations système (santé, feedback, configuration)"
        }
    ]
    
    # Organisation des routes par tags
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            if "websocket" in operation.get("description", "").lower():
                operation["tags"] = ["WebSocket"]
            elif any(keyword in operation.get("description", "").lower() 
                    for keyword in ["health", "feedback", "config"]):
                operation["tags"] = ["System"]
            else:
                operation["tags"] = ["Game"]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Fonction pour sérialiser l'état du jeu
def from_game_state(state: Any) -> dict:
    """
    Convert game state to JSON serializable format.
    Handles datetime objects and other special types.
    """
    if isinstance(state, dict) or hasattr(state, 'items'):
        # Gère à la fois les dict et les mappingproxy
        return {k: from_game_state(v) for k, v in dict(state).items()}
    elif isinstance(state, (list, tuple)):
        return [from_game_state(item) for item in state]
    elif isinstance(state, datetime):
        return state.isoformat()
    elif hasattr(state, "model_dump"):
        # Pour les modèles Pydantic v2
        return from_game_state(state.model_dump())
    elif hasattr(state, "dict"):
        # Pour les modèles Pydantic v1
        return from_game_state(state.dict())
    elif hasattr(state, "__dict__"):
        # Pour les objets Python standards
        return from_game_state(state.__dict__)
    else:
        # Convertir les types non-sérialisables en str si nécessaire
        try:
            json.dumps(state)
            return state
        except (TypeError, OverflowError):
            return str(state)

# WebSocket endpoint
@app.websocket("/ws/game")
async def websocket_endpoint(
    websocket: WebSocket,
    agent_mgr = Depends(get_agent_manager)
):
    """
    WebSocket endpoint for real-time game state updates.
    
    Handles:
    - Connection management
    - Real-time state updates
    - Game events broadcasting
    """
    logger.info("New WebSocket connection attempt")
    await manager.connect(websocket)
    try:
        logger.info("WebSocket connection established")
        
        # Envoyer l'état initial
        try:
            initial_state = await agent_mgr.get_state()
            if initial_state:
                await websocket.send_json(from_game_state(initial_state))
        except Exception as e:
            logger.error(f"Error sending initial state: {e}")
            await websocket.send_json({
                "error": str(e),
                "status": "error"
            })
        
        while True:
            if websocket.client_state == WebSocketState.DISCONNECTED:
                break
                
            try:
                data = await websocket.receive_json()
                logger.debug(f"Received WebSocket data: {data}")
                response = await agent_mgr.process_websocket_message(data)
                await websocket.send_json(from_game_state(response))
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await websocket.send_json({
                    "error": str(e),
                    "status": "error"
                })
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info("Cleaning up WebSocket connection")
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        manager.disconnect(websocket)

# Documentation des WebSockets
@app.get("/ws/info", include_in_schema=False)
async def websocket_info():
    """Redirection vers la documentation Socket.IO."""
    return {
        "message": "Pour la documentation Socket.IO, veuillez consulter socketio.py",
        "location": "/api/socketio.py"
    }

# Routes REST
@app.post("/api/game/action")
async def process_action(
    action: ActionRequest,
    agent_mgr = Depends(get_agent_manager)
) -> ActionResponse:
    """Process a game action."""
    try:
        logger.info(f"Processing action: {action}")
        result = await agent_mgr.process_action(action)
        logger.info("Action processed successfully")
        return ActionResponse(
            success=True,
            message="Action processed successfully",
            state=to_game_state(result)
        )
    except Exception as e:
        logger.error(f"Error processing action: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/game/state")
async def get_game_state(agent_mgr = Depends(get_agent_manager)) -> Dict[str, Any]:
    """Get current game state.
    
    Args:
        agent_mgr (AgentManager): Agent manager instance
        
    Returns:
        Dict[str, Any]: Current game state
    """
    try:
        state = await agent_mgr.get_current_state()
        return state
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e

@app.post("/feedback")
async def save_feedback(feedback: FeedbackRequest):
    """Save user feedback."""
    try:
        # TODO: Implement feedback storage
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error saving feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/health")
async def health_check(check_type: Optional[str] = None) -> HealthResponse:
    """Health check endpoint.
    
    Args:
        check_type (str, optional): Type of health check ('api', 'author'). Defaults to None.
    
    Returns:
        HealthResponse: Health status information
    """
    logger.info(f"Health check requested - Type: {check_type}")
    
    version = "1.0.0"  # TODO: Get from config
    timestamp = datetime.now().isoformat()
    
    if check_type == "author":
        message = "Author API is running"
    else:
        message = "API is running"
        
    return HealthResponse(
        status="ok",
        message=message,
        timestamp=timestamp,
        version=version,
        type=check_type
    )

@app.get("/roll/{dice_type}")
async def roll_game_dice(dice_type: str) -> DiceResult:
    """Roll game dice."""
    try:
        result = roll_dice(dice_type)
        return DiceResult(
            value=result,
            dice_type=dice_type
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/subscribe")
async def subscribe_to_game_updates(agent_mgr = Depends(get_agent_manager)):
    """Subscribe to game state updates."""
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

@app.post("/navigate/{section_number}")
async def navigate_to_section(
    section_number: int,
    agent_mgr = Depends(get_agent_manager)
):
    """Navigate to a specific section."""
    try:
        return await agent_mgr.navigate_to_section(section_number)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error navigating to section {section_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/navigate/{section_number}/stream")
async def navigate_to_section_with_updates(
    section_number: int,
    agent_mgr = Depends(get_agent_manager)
):
    """Navigate to a section with streaming updates."""
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

@app.post("/response")
async def submit_response(
    response: str,
    agent_mgr = Depends(get_agent_manager)
):
    """Submit a user response."""
    try:
        return await agent_mgr.submit_response(response)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing response: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/perform")
async def perform_action(
    action: Dict[str, Any],
    agent_mgr = Depends(get_agent_manager)
):
    """Perform a game action."""
    try:
        return await agent_mgr.perform_action(action)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error performing action: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/feedback")
async def get_feedback(agent_mgr = Depends(get_agent_manager)):
    """Get feedback about current game state."""
    try:
        return to_domain_feedback(await agent_mgr.get_feedback())
    except Exception as e:
        logger.error(f"Error getting feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Dans app.py
@app.post("/api/game/initialize")
async def initialize_game(agent_mgr=Depends(get_agent_manager)) -> Dict[str, Any]:
    """
    Initialize a new game session.

    Directly calls AgentManager's initialize_game to set up a new game session.
    """
    try:
        logger.info("Initializing a new game session")

        # Appelle initialize_game sans arguments
        initial_state = await agent_mgr.initialize_game()

        # Retourne l'état initial directement
        return initial_state.model_dump()

    except Exception as e:
        logger.error(f"Error initializing game: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/stop")
async def stop_game(
    agent_mgr = Depends(get_agent_manager)
) -> Dict[str, str]:
    """
    Stop the current game session and cleanup resources.
    
    This endpoint:
    1. Saves the final game state
    2. Saves trace data
    3. Cleans up resources
    4. Resets the story graph
    """
    try:
        logger.info("Stopping game session")
        await agent_mgr.stop_game()
        logger.info("Game session stopped successfully")
        return {"status": "success", "message": "Game session stopped successfully"}
        
    except Exception as e:
        logger.error(f"Error stopping game session: {e}")
        logger.error("Stack trace:", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Exception handler global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )
