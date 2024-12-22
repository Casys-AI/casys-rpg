"""
Decision Agent Protocol Module
Defines the interface for the Decision Agent
"""

from typing import Dict, Optional, List, Protocol, AsyncGenerator
from models.game_state import GameState
from agents.protocols.base_agent_protocol import BaseAgentProtocol

class DecisionAgentProtocol(BaseAgentProtocol, Protocol):
    """Protocol defining the interface for the Decision Agent."""
    
    async def analyze_decision(self, state: GameState) -> GameState:
        """
        Analyze user decisions and validate against rules.
        
        Args:
            state: Current game state
            
        Returns:
            GameState: Updated game state
        """
        ...
        
    async def validate_choice(self, choice: str, valid_choices: List[str]) -> bool:
        """
        Validate a user choice against available options.
        
        Args:
            choice: User's choice
            valid_choices: List of valid choices
            
        Returns:
            bool: True if choice is valid
        """
        ...
        
    async def format_response(self, response: str) -> str:
        """
        Format agent response for display.
        
        Args:
            response: Raw response to format
            
        Returns:
            str: Formatted response
        """
        ...

    async def ainvoke(self, input_data: Dict) -> AsyncGenerator[Dict, None]:
        """
        Asynchronous invocation interface.
        
        Args:
            input_data: Input data containing game state and user choice
            
        Yields:
            Dict: Decision processing results
        """
        ...
