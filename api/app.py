"""
API FastAPI pour le jeu interactif
"""

# Standard library imports
import os
from pathlib import Path
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# Third-party imports
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

# Local imports
from config.storage_config import StorageConfig
from config.game_config import GameConfig
from config.logging_config import get_logger
from managers.dependencies import get_agent_manager
from api.routes.rest import api_router_rest
from api.routes.ws import api_router_ws

from models.game_state import GameState
from models.errors_model import GameError, NarratorError, StateError, AgentError
from models.decision_model import DiceResult, DecisionModel
from models.character_model import CharacterModel
from models.trace_model import TraceModel

# Initialize logger
logger = get_logger('api')

# Configuration
API_HOST = os.getenv("CASYS_HOST", "127.0.0.1")  # IPv4 explicite
API_PORT = int(os.getenv("CASYS_PORT", "8000"))  # Port 8000 par défaut
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

# Add project root to PYTHONPATH
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Configuration globale
def get_storage_config() -> StorageConfig:
    """Get storage configuration."""
    return StorageConfig.get_default_config(BASE_DIR / "data")

# Gestionnaire de l'application
async def shutdown_event():
    """Cleanup API components."""
    try:
        # Get agent manager
        agent_mgr = get_agent_manager()
        
        # Cleanup agent manager
        if agent_mgr:
            logger.debug("Cleaning up AgentManager")
            await agent_mgr.stop_game()
        
        logger.info("API shutdown successfully")
    except Exception as e:
        logger.error(f"Failed to shutdown API: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan."""
    # Startup
    logger.info("Starting up...")
    yield
    # Shutdown
    logger.info("Shutting down...")
    await shutdown_event()

# Application FastAPI
app = FastAPI(
    title="CASYS RPG API",
    description="API pour le jeu de rôle CASYS",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # URL du frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

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
        - WebSocket pour la communication temps réel
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

# WebSocket info endpoint
@app.get("/ws/info", include_in_schema=False)
async def websocket_info():
    """Documentation WebSocket."""
    return {
        "message": "Pour la documentation WebSocket, veuillez consulter la documentation OpenAPI",
        "location": "/docs#/WebSocket"
    }

# Exception handler global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Global exception handler caught: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

# Inclusion des routers
app.include_router(api_router_rest)
app.include_router(api_router_ws)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level="info"
    )
