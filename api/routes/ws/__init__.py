"""
WebSocket routes.
"""
from fastapi import APIRouter
from .game_route_ws import game_router_ws

api_router_ws = APIRouter()
api_router_ws.include_router(game_router_ws)
