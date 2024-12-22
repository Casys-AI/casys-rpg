"""
State Manager Protocol
Defines the interface for state management.
"""
from typing import Protocol, Dict, Any, Optional, List, runtime_checkable, Union
from datetime import datetime
from models.game_state import GameState
from models.errors_model import StateError
from config.storage_config import StorageConfig
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
from .base_protocols import StorageProtocol

@runtime_checkable
class StateManagerProtocol(Protocol, StorageProtocol):
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
    
    def get_current_state(self) -> Optional[GameState]:
        """
        Get the current game state.
        
        Returns:
            Optional[GameState]: The current game state, or None if not initialized
        """
        ...
    
    def get_state_history(self) -> List[GameState]:
        """
        Get the history of game states.
        
        Returns:
            List[GameState]: List of previous game states
        """
        ...
    
    async def clear_state(self) -> None:
        """Clear the current game state."""
        ...
    
    def validate_state(self, state: GameState) -> Optional[StateError]:
        """
        Validate a game state.
        
        Args:
            state: The game state to validate
            
        Returns:
            Optional[StateError]: Error if state is invalid, None otherwise
        """
        ...
    
    async def create_initial_state(self) -> GameState:
        """
        Create and return an initial game state.
        
        Returns:
            GameState: A new initial game state
        """
        initial_state = GameState.create_initial_state()
        await self.save_state(initial_state)
        return initial_state
    
    async def create_error_state(self, error_message: str) -> StateError:
        """
        Create an error state with the given message.
        
        Args:
            error_message: Error message to include in the state
            
        Returns:
            StateError: Error state
        """
        error_state = GameState.create_error_state(error_message, current_state=self.current_state)
        await self.save_state(error_state)
        return error_state
    
    async def update_state(self, new_state: Dict | GameState) -> Optional[StateError]:
        """
        Update the current game state with validation.
        
        Args:
            new_state: New state to apply (Dict or GameState)
            
        Returns:
            Optional[StateError]: Error if update failed, None otherwise
        """
        ...
