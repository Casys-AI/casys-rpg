"""Base agent class for all game agents."""

from typing import Dict, Any, Optional, ClassVar
from pydantic import BaseModel, Field

from config.agents.agent_config_base import AgentConfigBase
from config.logging_config import get_logger
from agents.protocols.base_agent_protocol import BaseAgentProtocol
from models.agent_config_model import AgentConfigModel
import logging

class BaseAgent:
    """Base agent implementation."""
    logger: ClassVar = get_logger(__name__)

    @classmethod
    def create(cls, agent_type: str, config: AgentConfigBase, **kwargs) -> 'BaseAgent':
        """Create an agent instance.
        
        Args:
            agent_type: Type of agent to create ('rules', 'narrator', etc.)
            config: Configuration for the agent
            **kwargs: Additional arguments for specific agent types
            
        Returns:
            BaseAgent: Instance of the requested agent type
            
        Raises:
            ValueError: If agent_type is not recognized
        """
        # Lazy import to avoid circular dependencies
        if agent_type == "rules":
            from agents.rules_agent import RulesAgent
            return RulesAgent(config=config, rules_manager=kwargs.get('rules_manager'))
        elif agent_type == "narrator":
            from agents.narrator_agent import NarratorAgent
            return NarratorAgent(config=config, narrator_manager=kwargs.get('narrator_manager'))
        elif agent_type == "decision":
            from agents.decision_agent import DecisionAgent
            return DecisionAgent(config=config, decision_manager=kwargs.get('decision_manager'))
        elif agent_type == "trace":
            from agents.trace_agent import TraceAgent
            return TraceAgent(config=config, trace_manager=kwargs.get('trace_manager'))
        elif agent_type == "story":
            from agents.story_graph import StoryGraph
            return StoryGraph(config=config)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

    def __init__(self, config: AgentConfigBase):
        """Initialize BaseAgent.
        
        Args:
            config: Configuration for the agent
        """
        if not config:
            raise ValueError("config is required")
            
        # Store the raw config object
        if isinstance(config, dict):
            self.config = AgentConfigBase(**config)
        else:
            self.config = config
            
        # Setup logging
        self.config.setup_logging(self.__class__.__name__)

    async def initialize(self) -> None:
        """Initialize the agent."""
        pass

    async def ainvoke(self, input_data: Dict[str, Any]) -> Any:
        """
        Asynchronous invocation of the agent.
        
        Args:
            input_data: Input data for the agent
            
        Returns:
            Any: Processing results
        """
        raise NotImplementedError("ainvoke must be implemented by derived classes")

    async def invoke(self, input_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Synchronous invocation of the agent.
        
        Args:
            input_data: Input data for the agent
            config: Optional configuration override
            
        Returns:
            Dict[str, Any]: Processing results
        """
        raise NotImplementedError("invoke must be implemented by derived classes")

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

    def get_agent_name(self) -> str:
        """Get the name of the agent."""
        return self.__class__.__name__

# Register BaseAgent as implementing BaseAgentProtocol
BaseAgentProtocol.register(BaseAgent)
