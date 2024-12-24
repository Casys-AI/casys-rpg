"""
Protocol for trace manager implementations.
"""
from typing import Dict, Any, Protocol, runtime_checkable
from models.game_state import GameState

@runtime_checkable
class TraceManagerProtocol(Protocol):
    """Protocol defining the interface for trace managers."""
    
    async def start_session(self) -> None:
        """Start a new game session."""
        ...
        
    async def process_trace(self, state: GameState, action: Dict[str, Any]) -> None:
        """Process and store a game trace.
        
        Args:
            state: Current game state
            action: Action details including type and other data
        """
        ...
        
    async def save_trace(self) -> None:
        """Save current trace to storage."""
        ...
