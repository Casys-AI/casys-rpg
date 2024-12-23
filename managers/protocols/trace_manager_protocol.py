"""
Trace Manager Protocol
Defines the interface for game trace management.
"""
from typing import Dict, Optional, Any, List, Protocol, runtime_checkable
from models.game_state import GameState
from models.trace_model import TraceModel
from models.errors_model import TraceError
from config.storage_config import StorageConfig
from managers.protocols.cache_manager_protocol import CacheManagerProtocol

@runtime_checkable
class TraceManagerProtocol(Protocol):
    """Protocol for trace management operations."""
    
    def __init__(self, config: StorageConfig, cache_manager: CacheManagerProtocol) -> None:
        """Initialize trace manager."""
        ...
        
    async def start_session(self) -> None:
        """
        Start a new game session.
        
        Creates a new trace with a unique session ID and game ID.
        """
        ...
        
    async def process_trace(self, state: GameState, action: Dict[str, Any]) -> None:
        """
        Process and store a game trace.
        
        Args:
            state: Current game state
            action: Action details to trace
        """
        ...
        
    async def save_trace(self) -> None:
        """
        Save current trace to storage.
        
        Raises:
            TraceError: If save fails
        """
        ...
        
    async def get_current_trace(self) -> Optional[TraceModel]:
        """
        Get current trace if exists.
        
        Returns:
            Optional[TraceModel]: Current trace or None
        """
        ...
        
    async def get_trace_history(self) -> List[TraceModel]:
        """
        Get all traces from storage.
        
        Returns:
            List[TraceModel]: List of all traces
            
        Raises:
            TraceError: If loading fails
        """
        ...
        
    def get_state_feedback(self, state: GameState) -> str:
        """
        Get feedback about the current game state.
        
        Args:
            state: Current game state
            
        Returns:
            str: Formatted feedback about the state
        """
        ...
