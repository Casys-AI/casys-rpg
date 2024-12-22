"""Base configuration models."""
from typing import Dict, Any, TypeVar, Generic, Optional
from pydantic import BaseModel, Field

TConfig = TypeVar('TConfig', bound=BaseModel)

class ConfigModel(BaseModel, Generic[TConfig]):
    """Base configuration model for all components."""
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
    config: Optional[TConfig] = Field(
        default=None,
        description="Component specific configuration"
    )
