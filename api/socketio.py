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
    if not _socket_manager:
        _socket_manager = SocketManager(
            app=app,
            mount_location="/ws",
            cors_allowed_origins=["*"],  # En production, spécifier les origines exactes
            socketio_path="socket.io",
        )
        
        # Register event handlers
        @_socket_manager.on("connect")
        async def connect(sid: str):
            """Handle client connection."""
            print(f"Client connected: {sid}")
            await _socket_manager.emit('connection_response', {'status': 'connected'}, to=sid)

        @_socket_manager.on("disconnect")
        async def disconnect(sid: str):
            """Handle client disconnection."""
            print(f"Client disconnected: {sid}")
            # Clean up game session if exists
            for game_id, session in game_sessions.items():
                if sid in session.get('players', []):
                    session['players'].remove(sid)
                    if not session['players']:
                        del game_sessions[game_id]

        @_socket_manager.on("join_game")
        async def join_game(sid: str, data: Dict[str, Any]):
            """Handle player joining a game.
            
            Args:
                sid: Session ID
                data: Must contain game_id
            """
            game_id = data.get('game_id')
            if not game_id:
                await _socket_manager.emit('error', {'message': 'game_id is required'}, to=sid)
                return

            if game_id not in game_sessions:
                game_sessions[game_id] = {
                    'players': [],
                    'state': None,
                    'created_at': datetime.now()
                }
            
            if sid not in game_sessions[game_id]['players']:
                game_sessions[game_id]['players'].append(sid)
            
            await _socket_manager.emit('game_joined', {
                'game_id': game_id,
                'player_count': len(game_sessions[game_id]['players'])
            }, to=sid)

        @_socket_manager.on("player_input")
        async def player_input(sid: str, data: Dict[str, Any]):
            """Handle player input.
            
            Args:
                sid: Session ID
                data: Must contain game_id and input
            """
            game_id = data.get('game_id')
            player_input = data.get('input')
            
            if not game_id or not player_input:
                await _socket_manager.emit('error', {'message': 'game_id and input are required'}, to=sid)
                return
            
            if game_id not in game_sessions:
                await _socket_manager.emit('error', {'message': 'game not found'}, to=sid)
                return
            
            # Process player input and update game state
            # TODO: Implement game state update logic
            
            # Broadcast updated state to all players in the game
            await _socket_manager.emit('game_update', {
                'game_id': game_id,
                'state': game_sessions[game_id]['state']
            }, room=game_id)

        @_socket_manager.on("request_state")
        async def request_state(sid: str, data: Dict[str, Any]):
            """Handle request for current game state.
            
            Args:
                sid: Session ID
                data: Must contain game_id
            """
            game_id = data.get('game_id')
            
            if not game_id:
                await _socket_manager.emit('error', {'message': 'game_id is required'}, to=sid)
                return
            
            if game_id not in game_sessions:
                await _socket_manager.emit('error', {'message': 'game not found'}, to=sid)
                return
            
            await _socket_manager.emit('game_state', {
                'game_id': game_id,
                'state': game_sessions[game_id]['state']
            }, to=sid)
                
    return _socket_manager

def get_socketio_app() -> SocketManager:
    """Get the Socket.IO manager.
    
    Returns:
        SocketManager: The Socket.IO manager
    """
    if not _socket_manager:
        raise RuntimeError("Socket.IO manager not initialized. Call init_socketio first.")
    return _socket_manager
