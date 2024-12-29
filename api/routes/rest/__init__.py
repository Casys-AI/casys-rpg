"""
REST API routes.
"""
from fastapi import APIRouter
from .game_route_rest import game_router_rest
from .health_route_rest import health_router_rest
from .utils_route_rest import utils_router_rest

api_router_rest = APIRouter()
api_router_rest.include_router(game_router_rest)
api_router_rest.include_router(health_router_rest)
api_router_rest.include_router(utils_router_rest)
