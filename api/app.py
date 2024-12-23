"""
API FastAPI pour le jeu interactif
"""

import os
import sys
import logging
from typing import Dict, Any, List, AsyncGenerator
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path

# Add project root to PYTHONPATH
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from fastapi import FastAPI, WebSocket, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

# Add project root to PYTHONPATH
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from fastapi import FastAPI, WebSocket, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config.storage_config import StorageConfig
from models.game_state import GameState
from managers.agent_manager import AgentManager
from agents.factories.game_factory import GameFactory, GameAgents, GameManagers

import uuid
from api.socketio import init_socketio

from models.character_model import CharacterModel
from models.trace_model import TraceModel
from models.decision_model import DecisionModel, DiceResult

from config.game_config import GameConfig
from config.storage_config import StorageConfig, StorageFormat, NamespaceConfig
from utils.game_utils import roll_dice
from config.logging_config import get_logger

from api.dto.request_dto import GameInitRequest, FeedbackRequest, ActionRequest
from api.dto.response_dto import ActionResponse, GameResponse, HealthResponse
from api.dto.converters import to_game_state, from_game_state, to_domain_feedback

logger = get_logger('api')

# Configuration
#TODO enlever car dans .env et run.py
API_HOST = "127.0.0.1"
API_PORT = 8000
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

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
        if not _game_factory:
            _game_factory = GameFactory()
        if not _game_components:
            _game_components = _game_factory.create_game_components()
        agents, managers = _game_components
        _agent_manager = AgentManager(agents=agents, managers=managers)
    return _agent_manager

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
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les origines exactes
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
        # Initialize game components
        agent_manager = get_agent_manager()
        await agent_manager.initialize()
        logger.info("Game components initialized successfully")
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
        description="""
        API pour le jeu de rôle interactif Casys.
        
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

# WebSocket endpoint
@app.websocket("/ws")
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
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            response = await agent_mgr.process_websocket_message(data)
            await websocket.send_json(response)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)

# Documentation des WebSockets
@app.get("/ws/info", include_in_schema=False)
async def websocket_info():
    """Redirection vers la documentation Socket.IO."""
    return {
        "message": "Pour la documentation Socket.IO, veuillez consulter socketio.py",
        "location": "/api/socketio.py"
    }

# Routes REST
@app.post("/action")
async def process_action(
    action: ActionRequest,
    agent_mgr = Depends(get_agent_manager)
) -> ActionResponse:
    """Process a game action."""
    try:
        result = await agent_mgr.process_action(action)
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

@app.get("/health")
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="API is running"
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

@app.get("/state")
async def get_game_state(agent_mgr = Depends(get_agent_manager)):
    """Get current game state."""
    try:
        return to_game_state(await agent_mgr.get_state())
    except Exception as e:
        logger.error(f"Error getting game state: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/subscribe")
async def subscribe_to_game_updates(agent_mgr = Depends(get_agent_manager)):
    """Subscribe to game state updates."""
    try:
        return StreamingResponse(
            agent_mgr.subscribe_to_updates(),
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
        return await agent_mgr.process_response(response)
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

@app.post("/init")
async def initialize_game(
    init_request: GameInitRequest,
    agent_mgr = Depends(get_agent_manager)
) -> GameResponse:
    """
    Initialize a new game session.
    
    This endpoint:
    1. Creates a new game session with the specified ID
    2. Initializes the StoryGraph and all agents
    3. Sets up the initial game state
    4. Returns the session details and initial state
    """
    try:
        session_id = str(uuid.uuid4())
        game_factory = GameFactory()
        
        # Initialize game components
        story_graph = await game_factory.create_story_graph()
        rules_agent = await game_factory.create_rules_agent()
        decision_agent = await game_factory.create_decision_agent()
        narrator_agent = await game_factory.create_narrator_agent()
        trace_agent = await game_factory.create_trace_agent()
        
        # Initialize game state
        initial_state = await agent_mgr.initialize_game(
            session_id=session_id,
            story_graph=story_graph,
            rules_agent=rules_agent,
            decision_agent=decision_agent,
            narrator_agent=narrator_agent,
            trace_agent=trace_agent,
            init_params=init_request.dict()
        )
        
        return GameResponse(
            session_id=session_id,
            initial_state=to_game_state(initial_state)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error initializing game: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Exception handler global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": str(exc)}
    )

if __name__ == "__main__":
    logger.info(f"Starting API server on {API_HOST}:{API_PORT}")
    import uvicorn
    uvicorn.run(
        "app:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level="info"
    )
