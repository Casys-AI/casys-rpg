"""Base configuration for all game components."""
from typing import Dict, Any
from pydantic import BaseModel, Field

class ComponentConfig(BaseModel):
    """Base configuration class for all components."""
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    cache_enabled: bool = Field(
        default=True,
        description="Enable caching"
    )
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional options"
    )
