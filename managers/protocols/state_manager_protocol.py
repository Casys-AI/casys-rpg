"""
State Manager Protocol
Defines the interface for state management.
"""
from typing import Dict, Any, Optional, List, Union, Protocol, runtime_checkable
from datetime import datetime
from models.game_state import GameState
from models.errors_model import StateError
from config.storage_config import StorageConfig
from managers.protocols.cache_manager_protocol import CacheManagerProtocol

@runtime_checkable
class StateManagerProtocol(Protocol):
    """Protocol defining the interface for state management."""
    
    def __init__(self, config: StorageConfig, cache_manager: CacheManagerProtocol) -> None:
        """Initialize with configuration and cache manager."""
        ...
    
    @property
    def current_state(self) -> Optional[GameState]:
        """Get current game state."""
        ...
    
    async def initialize(self, game_id: Optional[str] = None) -> None:
        """Initialize the state manager and generate game_id.
        
        Args:
            game_id: Optional game ID to use. If not provided, a new one will be generated.
        """
        ...
    
    async def get_game_id(self) -> Optional[str]:
        """Get current game ID."""
        ...
    
    async def save_state(self, state: GameState) -> GameState:
        """
        Save the current game state.
        
        Args:
            state: The game state to save
            
        Returns:
            GameState: The saved game state
            
        Raises:
            StateError: If validation or save fails
        """
        ...

    async def load_state(self, section_number: int) -> Optional[GameState]:
        """
        Load state for a specific section.
        
        Args:
            section_number: Section number to load
            
        Returns:
            Optional[GameState]: Loaded state if exists
            
        Raises:
            StateError: If load fails
        """
        ...

    async def get_current_state(self) -> Optional[GameState]:
        """
        Get the current game state.
        
        Returns:
            Optional[GameState]: The current game state, or None if not found
            
        Raises:
            StateError: If retrieval fails
        """
        ...
    
    async def clear_state(self) -> None:
        """Clear current state."""
        ...
    
    async def get_session(self, game_id: str) -> str:
        """Get or create session ID for a game.
        
        Args:
            game_id: The game ID to get/create session for
            
        Returns:
            str: The session ID
        """
        ...

    async def create_initial_state(self, session_id: str, **init_params: Dict[str, Any]) -> GameState:
        """Create and return initial game state.
        
        Args:
            session_id: Unique session identifier
            **init_params: Additional initialization parameters
            
        Returns:
            GameState: Initial state
            
        Raises:
            StateError: If creation fails
        """
        ...
    
    async def create_error_state(self, error_message: str) -> GameState:
        """
        Create error state.
        
        Args:
            error_message: Error message
            
        Returns:
            GameState: Error state
            
        Raises:
            StateError: If creation fails
        """
        ...
    
    async def bind_session(self, game_id: str, session_id: str) -> None:
        """Bind an existing session ID to a game ID."""
        ...

    def get_current_timestamp(self) -> str:
        """
        Get current timestamp in ISO format.
        
        Returns:
            str: Current timestamp in ISO format
        """
        ...
