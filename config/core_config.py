"""Core configurations for all components."""
from typing import Dict, Any, TypeVar, Generic
from pydantic import BaseModel, Field, ConfigDict
import os

T = TypeVar('T')

class CoreConfig(BaseModel):
    """Base configuration for all components."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    debug: bool = Field(
        default=bool(os.getenv("DEBUG", "False")),
        description="Enable debug mode"
    )
    cache_enabled: bool = Field(
        default=True,
        description="Enable caching"
    )

class ComponentConfig(CoreConfig, Generic[T]):
    """Generic configuration for a component with dependencies."""
    dependencies: Dict[str, T] = Field(
        default_factory=dict,
        description="Component dependencies"
    )
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional options"
    )
