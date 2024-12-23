"""
Base Agent Protocol Module
Defines the base protocol for all game agents.
"""

from typing import Dict, Optional, AsyncGenerator, Protocol, Any, runtime_checkable
from models.game_state import GameState

@runtime_checkable
class BaseAgentProtocol(Protocol):
    """Protocol defining the common interface for all agents."""
    
    async def ainvoke(self, input_data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Asynchronous invocation of the agent.
        
        Args:
            input_data: Input data for the agent
            
        Yields:
            Dict[str, Any]: Processing results
        """
        ...
        
    async def invoke(self, input_data: Dict, config: Optional[Dict] = None) -> Dict[str, GameState]:
        """
        Synchronous invocation of the agent.
        
        Args:
            input_data: Input data for the agent
            config: Optional configuration
            
        Returns:
            Dict[str, GameState]: Processing results and updated game state
        """
        ...

    async def process(self, context: Dict[str, Any], state: GameState) -> Dict[str, Any]:
        """
        Process a request in the context of the current game state.
        
        Args:
            context: Dictionary containing request context
            state: Current game state
            
        Returns:
            Dict[str, Any]: Response from the agent
        """
        ...
    
    def validate_response(self, response: Dict[str, Any]) -> bool:
        """
        Validate agent response.
        
        Args:
            response: Response to validate
            
        Returns:
            bool: True if response is valid, False otherwise
        """
        ...
    
    def get_system_prompt(self) -> str:
        """
        Get the agent's system prompt.
        
        Returns:
            str: System prompt for the agent
        """
        ...
    
    def update_config(self, config_updates: Dict[str, Any]) -> None:
        """
        Update agent configuration.
        
        Args:
            config_updates: Dictionary of configuration updates
        """
        ...

    def get_agent_id(self) -> str:
        """Get unique agent identifier."""
        ...
    
    def get_agent_type(self) -> str:
        """Get agent type identifier."""
        ...
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Get agent configuration."""
        ...
