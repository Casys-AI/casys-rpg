"""
Decision Agent Protocol Module
Defines the interface for the Decision Agent
"""

from typing import Dict, List, Protocol, runtime_checkable
from models.game_state import GameState
from agents.protocols.base_agent_protocol import BaseAgentProtocol

@runtime_checkable
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
