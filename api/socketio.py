"""
Socket.IO implementation for the game API.

For testing and examples, see /static/socketio.html
"""

from typing import Dict, Any
from datetime import datetime
from fastapi_socketio import SocketManager
from fastapi import FastAPI
from models.game_state import GameState
from models.trace_model import ActionType
import logging

logger = logging.getLogger(__name__)

# Store active game sessions
game_sessions: Dict[str, Dict[str, Any]] = {}

# Socket.IO manager instance
_socket_manager: SocketManager | None = None

def init_socketio(app: FastAPI) -> SocketManager:
    """Initialize Socket.IO manager.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        SocketManager: Initialized Socket.IO manager
    """
    global _socket_manager
    
    if _socket_manager is None:
        logger.info("Initializing Socket.IO manager")
        _socket_manager = SocketManager(
            app=app,
            mount_location="/socket.io",
            cors_allowed_origins=[
                "http://localhost:9000",
                "http://127.0.0.1:9000",
                "http://localhost:8000",
                "http://127.0.0.1:8000",
                "http://localhost:5173"
            ],
            socketio_path="",
            async_mode="asgi"
        )
        
        # Register event handlers
        @_socket_manager.on("connect")
        async def connect(sid: str):
            """Handle client connection."""
            logger.info(f"Socket.IO client connected: {sid}")
            await _socket_manager.emit('connection_response', {'status': 'connected'}, to=sid)

        @_socket_manager.on("disconnect")
        async def disconnect(sid: str):
            """Handle client disconnection."""
            logger.info(f"Socket.IO client disconnected: {sid}")
            # Clean up game session if exists
            for game_id, session in game_sessions.items():
                if sid in session.get('players', []):
                    session['players'].remove(sid)
                    if not session['players']:
                        del game_sessions[game_id]
                    break

        @_socket_manager.on("join_game")
        async def join_game(sid: str, data: Dict[str, Any]):
            """Handle game join request."""
            game_id = data.get('game_id')
            if not game_id:
                logger.warning(f"Join game attempt without game_id from {sid}")
                await _socket_manager.emit('error', {'message': 'Game ID required'}, to=sid)
                return
                
            if game_id not in game_sessions:
                logger.info(f"Creating new game session {game_id}")
                game_sessions[game_id] = {
                    'players': [],
                    'created_at': datetime.now()
                }
            
            if sid not in game_sessions[game_id]['players']:
                game_sessions[game_id]['players'].append(sid)
                logger.info(f"Player {sid} joined game {game_id}")
            
            await _socket_manager.emit('game_joined', {'game_id': game_id}, to=sid)
            
        @_socket_manager.on("game_action")
        async def game_action(sid: str, data: Dict[str, Any]):
            """Handle game action."""
            game_id = data.get('game_id')
            action = data.get('action')
            
            if not game_id or not action:
                logger.warning(f"Invalid game action from {sid}: {data}")
                await _socket_manager.emit('error', {'message': 'Invalid action data'}, to=sid)
                return
                
            if game_id not in game_sessions:
                logger.warning(f"Game action for non-existent game {game_id} from {sid}")
                await _socket_manager.emit('error', {'message': 'Game not found'}, to=sid)
                return
                
            logger.info(f"Broadcasting game action in {game_id}: {action}")
            # Broadcast action to all players in the game
            for player_sid in game_sessions[game_id]['players']:
                await _socket_manager.emit('game_update', {
                    'game_id': game_id,
                    'action': action,
                    'timestamp': datetime.now().isoformat()
                }, to=player_sid)
                
        logger.info("Socket.IO manager initialized successfully")
    return _socket_manager

def get_socketio_manager() -> SocketManager:
    """Get the Socket.IO manager.
    
    Returns:
        SocketManager: The Socket.IO manager
    """
    if not _socket_manager:
        raise RuntimeError("Socket.IO manager not initialized")
    return _socket_manager
