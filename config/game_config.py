"""Game configuration module."""
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

from config.game_constants import (
    GameMode, 
    DEFAULT_CONFIG,
    ModelType,
    DEFAULT_TEMPERATURE,
    CACHE_CONFIG
)

from config.storage_config import StorageConfig

# Agent configs - chaque agent a sa propre config
from config.agents.narrator_agent_config import NarratorAgentConfig
from config.agents.rules_agent_config import RulesAgentConfig
from config.agents.decision_agent_config import DecisionAgentConfig
from config.agents.trace_agent_config import TraceAgentConfig
from config.agents.agent_config_base import AgentConfigBase

@dataclass
class AgentConfigs:
    """Container for all agent configurations."""
    narrator_config: NarratorAgentConfig
    rules_config: RulesAgentConfig
    decision_config: DecisionAgentConfig
    trace_config: TraceAgentConfig
    story_graph_config: AgentConfigBase = field(default_factory=AgentConfigBase)

@dataclass
class ManagerConfigs:
    """Container for all manager configurations.
    Note: All managers use StorageConfig as their base configuration.
    Some managers have additional specific configurations.
    """
    storage_config: StorageConfig  # Config de base utilisée par tous les managers
    character_config: Optional[StorageConfig] = None
    trace_config: Optional[StorageConfig] = None
    rules_config: Optional[StorageConfig] = None
    decision_config: Optional[StorageConfig] = None

class GameConfig(BaseModel):
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
    
    # LLM settings
    model_type: ModelType = Field(
        default=ModelType.NARRATOR,
        description="Default LLM model type"
    )
    temperature: float = Field(
        default=DEFAULT_TEMPERATURE,
        description="LLM temperature setting"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key"
    )
    
    # Component configurations
    agent_configs: Optional[AgentConfigs] = None
    manager_configs: Optional[ManagerConfigs] = None
    
    # Optional overrides
    config_overrides: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration overrides for specific components"
    )
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        arbitrary_types_allowed = True
    
    @classmethod
    def create_default(cls) -> "GameConfig":
        """Create a default game configuration."""
        storage_config = StorageConfig(**CACHE_CONFIG)  # Utilise CACHE_CONFIG pour storage_config
        return cls(
            agent_configs=cls._create_default_agent_configs(),
            manager_configs=cls._create_default_manager_configs(storage_config)
        )
    
    @classmethod
    def _create_default_agent_configs(cls) -> AgentConfigs:
        """Create default agent configurations."""
        return AgentConfigs(
            narrator_config=NarratorAgentConfig(model=ModelType.NARRATOR),
            rules_config=RulesAgentConfig(model=ModelType.RULES),
            decision_config=DecisionAgentConfig(model=ModelType.DECISION),
            trace_config=TraceAgentConfig(model=ModelType.TRACE)
        )
    
    @classmethod
    def _create_default_manager_configs(cls, storage_config: StorageConfig) -> ManagerConfigs:
        """Create default manager configurations.
        
        Args:
            storage_config: Base storage configuration used by all managers
        """
        return ManagerConfigs(
            storage_config=storage_config,
            # Les autres configs sont optionnelles car elles utilisent storage_config par défaut
        )
    
    def get_component_config(self, component_name: str) -> Dict[str, Any]:
        """Get configuration for a specific component with overrides."""
        # First try to get from agent configs
        if self.agent_configs:
            config = getattr(self.agent_configs, f"{component_name}_config", None)
            if config:
                return self._apply_overrides(component_name, config.model_dump())
        
        # Then try manager configs
        if self.manager_configs:
            # Si c'est un manager qui utilise storage_config par défaut
            specific_config = getattr(self.manager_configs, f"{component_name}_config", None)
            if specific_config:
                config_dict = specific_config.model_dump()
            else:
                # Utilise storage_config par défaut
                config_dict = self.manager_configs.storage_config.model_dump()
            
            return self._apply_overrides(component_name, config_dict)
        
        return {}
    
    def _apply_overrides(self, component_name: str, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply configuration overrides for a component."""
        if self.config_overrides and component_name in self.config_overrides:
            base_config.update(self.config_overrides[component_name])
        return base_config
