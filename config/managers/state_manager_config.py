"""State Manager configuration."""
from typing import Dict, Any
from pydantic import Field

from config.managers.manager_config_base import ManagerConfigBase

class StateManagerConfig(ManagerConfigBase):
    """Configuration for the State Manager."""
    
    # State persistence
    auto_save: bool = Field(
        default=True,
        description="Automatically save state"
    )
    save_interval: int = Field(
        default=60,
        description="Auto-save interval in seconds"
    )
    max_saves: int = Field(
        default=5,
        description="Maximum number of save states to keep"
    )
    
    # State validation
    validate_transitions: bool = Field(
        default=True,
        description="Validate state transitions"
    )
    strict_mode: bool = Field(
        default=False,
        description="Enforce strict state validation"
    )
    
    # Recovery options
    enable_recovery: bool = Field(
        default=True,
        description="Enable state recovery"
    )
    recovery_points: int = Field(
        default=3,
        description="Number of recovery points to maintain"
    )
