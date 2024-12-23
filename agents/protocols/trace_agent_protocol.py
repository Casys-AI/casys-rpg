"""
Trace Agent Protocol Module
Defines the interface for the Trace Agent
"""

from typing import Dict, Protocol, runtime_checkable
from models.game_state import GameState
from models.trace_model import TraceModel
from agents.protocols.base_agent_protocol import BaseAgentProtocol

@runtime_checkable
class TraceAgentProtocol(BaseAgentProtocol, Protocol):
    """Protocol defining the interface for the Trace Agent."""
    
    async def record_state(self, state: GameState) -> TraceModel:
        """
        Record current game state.
        
        Args:
            state: Current game state to record
            
        Returns:
            TraceModel: Updated trace information
        """
        ...
        
    async def analyze_state(self, state: GameState) -> GameState:
        """
        Analyze state and add insights.
        
        Args:
            state: Current game state to analyze
            
        Returns:
            GameState: State with analysis and insights
        """
        ...
