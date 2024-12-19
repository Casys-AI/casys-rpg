"""Game configuration module."""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from config.component_config import ComponentConfig
from config.game_constants import GameMode, DEFAULT_CONFIG

class GameConfig(ComponentConfig):
    """Main game configuration."""
    
    # Game settings
    mode: GameMode = Field(
        default=GameMode.NORMAL,
        description="Game operation mode"
    )
    debug_level: int = Field(
        default=0,
        description="Debug verbosity level"
    )
    
    # Performance settings
    max_retries: int = Field(
        default=DEFAULT_CONFIG["max_retries"],
        description="Maximum retry attempts for operations"
    )
    timeout_seconds: int = Field(
        default=DEFAULT_CONFIG["timeout_seconds"],
        description="Operation timeout in seconds"
    )
    
    # Component configurations
    agent_configs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Agent-specific configurations"
    )
    manager_configs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Manager-specific configurations"
    )
    
    # Optional overrides
    config_overrides: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration overrides for specific components"
    )
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        
    def get_component_config(self, component_name: str) -> Dict[str, Any]:
        """Get configuration for a specific component."""
        base_config = (
            self.agent_configs.get(component_name) or 
            self.manager_configs.get(component_name) or 
            {}
        )
        
        if self.config_overrides and component_name in self.config_overrides:
            base_config.update(self.config_overrides[component_name])
            
        return base_config
