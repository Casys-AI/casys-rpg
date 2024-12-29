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

game_router_ws = APIRouter()  # Enlever le préfixe /api pour les WebSockets

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
    - Heartbeat (ping/pong)
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
                
                # Gérer les pings
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": _json_serial(data.get("timestamp"))
                    })
                    continue
                
                # Traiter les messages du client
                if data.get("type") == "get_state":
                    current_state = await agent_mgr.get_state()
                    if current_state:
                        state_dict = from_game_state(current_state)
                        await websocket.send_text(
                            json.dumps(state_dict, default=_json_serial)
                        )
                
                elif data.get("type") == "choice":
                    logger.info("Processing user choice")
                    try:
                        choice = data.get("choice")
                        logger.debug(f"Received choice data: {data}")
                        if not choice:
                            raise ValueError("No choice provided")
                            
                        # Process le choix avec process_game_state
                        logger.info(f"Processing choice: {choice}")
                        new_state = await agent_mgr.process_game_state(
                            user_input=choice
                        )
                        
                        if new_state:
                            # Broadcast le nouvel état à tous les clients
                            logger.info("Broadcasting new state after choice")
                            state_dict = from_game_state(new_state)
                            await ws_manager.broadcast(state_dict)
                        else:
                            raise ValueError("No state returned after processing choice")
                            
                    except Exception as e:
                        logger.error(f"Error processing choice: {e}")
                        await websocket.send_json({
                            "error": str(e),
                            "status": "error",
                            "type": "choice_error"
                        })
                
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await websocket.send_json({
                    "error": str(e),
                    "status": "error"
                })
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await ws_manager.handle_error(websocket)
    finally:
        ws_manager.disconnect(websocket)
        logger.info("WebSocket connection closed")
