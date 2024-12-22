"""
Trace Manager Protocol
Defines the interface for trace management.
"""
from typing import Protocol, Dict, Any, Optional, runtime_checkable
from models.game_state import GameState
from config.storage_config import StorageConfig
from models.trace_model import TraceModel

@runtime_checkable
class TraceManagerProtocol(Protocol):
    """Protocol defining the interface for trace management."""
    
    def __init__(self, config: StorageConfig) -> None:
        """Initialize with configuration."""
        ...
    
    async def start_session(self) -> None:
        """Start a new game session."""
        ...
    
    async def process_trace(self, state: GameState, action: Dict[str, Any]) -> None:
        """
        Process and store trace.
        
        Args:
            state: Current game state
            action: Action to record
        """
        ...
    
    async def get_current_trace(self) -> TraceModel:
        """
        Get current trace.
        
        Returns:
            TraceModel: Current trace or new trace if none exists
        """
        ...
    
    def get_state_feedback(self, state: GameState) -> str:
        """
        Get feedback about the current game state.
        
        Args:
            state: Current game state
            
        Returns:
            str: Feedback about the current state
        """
        ...
