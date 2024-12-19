"""Base agent class for all game agents."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, ClassVar, AsyncGenerator
from pydantic import Field, ConfigDict

from config.agents.agent_config_base import AgentConfigBase
from config.logging_config import get_logger
from agents.protocols import BaseAgentProtocol
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
import logging

class BaseAgent(BaseAgentProtocol):
    """Classe de base pour tous les agents."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: AgentConfigBase = Field(default_factory=AgentConfigBase)
    cache_manager: Optional[CacheManagerProtocol] = None
    logger: ClassVar = get_logger(__name__)

    def __init__(self, config: AgentConfigBase, cache_manager: CacheManagerProtocol):
        """Initialize BaseAgent.
        
        Args:
            config: Configuration for the agent
            cache_manager: Cache manager instance
        """
        if not config:
            raise ValueError("config is required")
        if not cache_manager:
            raise ValueError("cache_manager is required")
            
        self.config = config
        self.cache_manager = cache_manager
        self.config.setup_logging(self.__class__.__name__)

    async def ainvoke(self, input_data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Asynchronous invocation of the agent.
        
        Args:
            input_data (Dict[str, Any]): Input data for the agent
            
        Returns:
            AsyncGenerator[Dict[str, Any], None]: Generator yielding updated states
        """
        raise NotImplementedError("Subclasses must implement ainvoke")

    async def invoke(self, input_data: Dict, config: Optional[Dict] = None) -> Dict[str, 'GameState']:
        """
        Invoke sync.
        
        Args:
            input_data (Dict): Input data containing game state
            config (Optional[Dict]): Optional configuration
            
        Returns:
            Dict[str, GameState]: Updated game state
        """
        raise NotImplementedError("Subclasses must implement invoke")
