"""
State Manager Protocol
Defines the interface for state management.
"""
from typing import Dict, Any, Optional, Protocol, runtime_checkable
from models.game_state import GameState
from models.errors_model import StateError
from config.storage_config import StorageConfig
from managers.protocols.cache_manager_protocol import CacheManagerProtocol

@runtime_checkable
class StateManagerProtocol(Protocol):
    """Protocol defining the interface for state management."""
    
    def __init__(self, config: StorageConfig, cache_manager: CacheManagerProtocol) -> None:
        """Initialize with configuration and cache manager.
        
        Args:
            config: Storage configuration
            cache_manager: Cache manager for state storage
        """
        ...
    
    async def initialize(self, game_id: Optional[str] = None) -> None:
        """Initialize state manager and generate game ID.
        
        Args:
            game_id: Optional game ID to use. If not provided, a new one will be generated.
        """
        ...
    
    @property
    def game_id(self) -> Optional[str]:
        """Get current game ID."""
        ...
    
    async def get_game_id(self) -> Optional[str]:
        """Get current game ID."""
        ...
    
    @staticmethod
    def generate_session_id() -> str:
        """Generate a unique session ID."""
        ...
    
    @property
    def current_state(self) -> Optional[GameState]:
        """Get current game state."""
        ...
    
    async def save_state(self, state: GameState) -> GameState:
        """Save state with basic validation.
        
        Args:
            state: State to save
            
        Returns:
            GameState: Saved state
            
        Raises:
            StateError: If validation or save fails
        """
        ...
    
    async def load_state(self, section_number: int) -> Optional[GameState]:
        """Load state for a specific section.
        
        Args:
            section_number: Section number to load
            
        Returns:
            Optional[GameState]: Loaded state if exists
            
        Raises:
            StateError: If load fails
        """
        ...
    
    async def get_current_state(self) -> Optional[GameState]:
        """Get current game state."""
        ...
    
    async def clear_state(self) -> None:
        """Clear current state."""
        ...
    
    async def create_initial_state(self, **init_params: Dict[str, Any]) -> GameState:
        """Create and return the initial game state.
        
        Args:
            **init_params: Additional parameters for initializing the state
            
        Returns:
            GameState: The initial state
        """
        ...
    
    async def create_error_state(self, error_message: str) -> GameState:
        """Create error state.
        
        Args:
            error_message: Error message
            
        Returns:
            GameState: Error state
            
        Raises:
            StateError: If creation fails
        """
        ...
    
    def get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format.
        
        Returns:
            str: Current timestamp in ISO format
        """
        ...
