"""Base agent class for all game agents."""
from abc import ABC
from typing import Dict, Any, Optional, ClassVar
from pydantic import Field, ConfigDict

from config.agents.agent_config_base import AgentConfigBase
from config.logging_config import get_logger
from agents.protocols.base_agent_protocol import BaseAgentProtocol
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
import logging

class BaseAgent(ABC):
    """Classe de base pour tous les agents."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: AgentConfigBase = Field(default_factory=AgentConfigBase)
    cache_manager: Optional[CacheManagerProtocol] = None
    logger: ClassVar = get_logger(__name__)

    def __init__(self, config: AgentConfigBase, cache_manager: Optional[CacheManagerProtocol] = None):
        """Initialize BaseAgent.
        
        Args:
            config: Configuration for the agent
            cache_manager: Optional cache manager instance
        """
        if not config:
            raise ValueError("config is required")
            
        self.config = config
        self.cache_manager = cache_manager
        self.config.setup_logging(self.__class__.__name__)

    def initialize(self) -> None:
        """Initialize the agent."""
        pass

    def get_system_prompt(self) -> str:
        """Get the agent's system prompt."""
        return self.config.system_message

    def update_config(self, config_updates: Dict[str, Any]) -> None:
        """Update agent configuration."""
        for key, value in config_updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def validate_response(self, response: Dict[str, Any]) -> bool:
        """Validate agent response."""
        return True  # Base implementation always validates
