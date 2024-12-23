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
    
    async def initialize(self) -> None:
        """Initialize the state manager and generate game_id."""
        ...
    
    async def save_state(self, state: GameState) -> Optional[StateError]:
        """
        Save the current game state.
        
        Args:
            state: The game state to save
            
        Returns:
            Optional[StateError]: Error if save failed, None otherwise
        """
        ...
    
    async def load_state(self, section_number: int) -> Union[GameState, StateError]:
        """
        Load state for a specific section.
        
        Args:
            section_number: Section number to load
            
        Returns:
            Union[GameState, StateError]: The loaded game state, or StateError if not found
        """
        ...
    
    async def create_error_state(self, error_message: str) -> GameState:
        """
        Create an error state with the given message.
        
        Args:
            error_message: Error message to include in the state
            
        Returns:
            GameState: The created error state
        """
        ...
    
    def get_storage_path(self) -> str:
        """Get storage path for state files."""
        ...
    
    def get_storage_options(self) -> Dict[str, Any]:
        """Get storage options for state management."""
        ...
