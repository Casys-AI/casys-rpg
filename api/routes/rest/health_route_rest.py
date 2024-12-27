"""
Health check endpoints.
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter
from loguru import logger
from api.dto.response_dto import HealthResponse

health_router_rest = APIRouter(prefix="/api", tags=["health"])

@health_router_rest.get("/health")
async def health_check(check_type: Optional[str] = None) -> HealthResponse:
    """
    Health check endpoint.
    
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
