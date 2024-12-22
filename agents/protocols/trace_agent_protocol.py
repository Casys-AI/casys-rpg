"""
Trace Agent Protocol Module
Defines the interface for the Trace Agent
"""

from typing import Dict, Optional, List, AsyncGenerator, Protocol, Any
from models.game_state import GameState
from models.trace_model import TraceModel
from agents.protocols.base_agent_protocol import BaseAgentProtocol

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

    async def ainvoke(self, input_data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Asynchronous invocation interface.
        
        Args:
            input_data: Input data containing game state
            
        Yields:
            Dict[str, Any]: Updated state with trace information
        """
        ...
