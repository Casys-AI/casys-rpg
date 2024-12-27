"""
WebSocket endpoints for game state management.
"""
from fastapi import WebSocket, WebSocketDisconnect, Depends, status
from fastapi.routing import APIRouter
from starlette.websockets import WebSocketState
from managers.agent_manager import AgentManager
from managers.dependencies import get_agent_manager
from api.utils.serialization_utils import from_game_state, _json_serial
import json
from loguru import logger

game_router_ws = APIRouter()

# WebSocket connection manager
class GameWSConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message, default=_json_serial))
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                await self.handle_error(connection)

    async def handle_error(self, websocket: WebSocket):
        """Handle WebSocket errors."""
        try:
            if websocket.client_state != WebSocketState.DISCONNECTED:
                await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except Exception as e:
            logger.error(f"Error closing WebSocket: {e}")
        finally:
            self.disconnect(websocket)

ws_manager = GameWSConnectionManager()

@game_router_ws.websocket("/ws/game")
async def game_websocket_endpoint(
    websocket: WebSocket,
    agent_mgr: AgentManager = Depends(get_agent_manager)
):
    """
    WebSocket endpoint for real-time game state updates.
    
    Handles:
    - Connection management
    - Real-time state updates
    - Game events broadcasting
    """
    logger.info("New WebSocket connection attempt")
    try:
        await ws_manager.connect(websocket)
        logger.info("WebSocket connection established")
        
        # Envoyer l'état initial
        try:
            initial_state = await agent_mgr.get_state()
            if initial_state:
                state_dict = from_game_state(initial_state)
                await websocket.send_text(
                    json.dumps(state_dict, default=_json_serial)
                )
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
                
                # Traiter les messages du client
                if data.get("type") == "get_state":
                    current_state = await agent_mgr.get_state()
                    if current_state:
                        state_dict = from_game_state(current_state)
                        await websocket.send_text(
                            json.dumps(state_dict, default=_json_serial)
                        )
                
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
        await ws_manager.handle_error(websocket)
