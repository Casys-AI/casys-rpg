"""
State Manager Protocol
Defines the interface for state management.
"""
from typing import Dict, Any, Optional, Protocol, runtime_checkable, Union
from models.game_state import GameState
from models.errors_model import StateError
from config.storage_config import StorageConfig
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
from managers.protocols.character_manager_protocol import CharacterManagerProtocol

@runtime_checkable
class StateManagerProtocol(Protocol):
    """Protocol defining the interface for state management."""
    
    def __init__(
        self, 
        config: StorageConfig, 
        cache_manager: CacheManagerProtocol,
        character_manager: CharacterManagerProtocol
    ) -> None:
        """Initialize with configuration and cache manager.
        
        Args:
            config: Storage configuration
            cache_manager: Cache manager for state storage
            character_manager: Character manager for character operations
        """
        ...
    
    async def initialize(self) -> None:
        """Initialize state manager.
        Sets up any necessary resources and state.
        """
        ...

    async def create_initial_state(
        self, 
        input_data: Optional[Union[Dict[str, Any], GameState]] = None
    ) -> GameState:
        """Create and initialize a new game state.
        
        This method handles:
        1. Generation of new session_id and game_id if needed
        2. Validation and merging of input data
        3. Creation of a proper GameState instance
        
        Args:
            input_data: Optional initial state data to merge
                       Can be either a dict or GameState instance
        
        Returns:
            GameState: The newly created and initialized state
            
        Raises:
            StateError: If state creation or validation fails
        """
        ...
    
    async def validate_state(
        self, 
        state_data: Union[Dict[str, Any], GameState]
    ) -> GameState:
        """Validate and convert state data to GameState.
        
        Args:
            state_data: State data to validate
                       Can be either a dict or GameState instance
            
        Returns:
            GameState: Validated state instance
            
        Raises:
            StateError: If validation fails
        """
        ...
        
    async def create_error_state(
        self, 
        error_message: str,
        current_state: Optional[GameState] = None
    ) -> GameState:
        """Create an error state from the current state.
        
        Args:
            error_message: Error message to include
            current_state: Optional current state to base error on
            
        Returns:
            GameState: Error state instance
        """
        ...

    async def get_game_id(self) -> Optional[str]:
        """Get the current game ID if any.
        
        Returns:
            Optional[str]: Current game ID or None if not set
        """
        ...

    async def save_state(self, state: GameState) -> None:
        """Save the current game state.
        
        Args:
            state: State to save
            
        Raises:
            StateError: If save fails
        """
        ...

    async def load_state(self, game_id: str) -> GameState:
        """Load a game state by ID.
        
        Args:
            game_id: ID of the game state to load
            
        Returns:
            GameState: Loaded state
            
        Raises:
            StateError: If load fails or state not found
        """
        ...

    @property
    def game_id(self) -> Optional[str]:
        """Get current game ID."""
        ...
    
    @property
    def current_state(self) -> Optional[GameState]:
        """Get current game state."""
        ...
    
    async def get_current_state(self) -> Optional[GameState]:
        """Get current game state."""
        ...
    
    async def clear_state(self) -> None:
        """Clear current state."""
        ...

    async def clear_model_nodes(self) -> None:
        """Clear all model nodes in the current state.
        This ensures that old model instances are properly destroyed
        before creating new ones.
        """
        ...

    def get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format.
        
        Returns:
            str: Current timestamp in ISO format
        """
        ...
