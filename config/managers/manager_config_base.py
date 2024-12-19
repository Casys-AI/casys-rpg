"""Base configuration for all managers."""
from typing import Dict, Any
from pydantic import Field

from config.component_config import ComponentConfig

class ManagerConfigBase(ComponentConfig):
    """Base configuration class for all managers."""
    manager_id: str = Field(
        default="",
        description="Unique identifier for the manager"
    )
    persistence_enabled: bool = Field(
        default=True,
        description="Enable data persistence"
    )
    manager_options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Manager-specific options"
    )
