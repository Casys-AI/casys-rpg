"""
State Manager Module
Manages game state persistence and validation.
"""

from typing import Dict, Optional, Any
from pydantic import BaseModel, ValidationError
import json
import logging
from datetime import datetime
import uuid
from loguru import logger

from models.game_state import GameState, GameStateInput, GameStateOutput
from config.storage_config import StorageConfig
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
from managers.protocols.state_manager_protocol import StateManagerProtocol
from models.errors_model import StateError

def _json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

class StateManager(StateManagerProtocol):
    """Manages game state persistence and basic validation."""
    
    def __init__(self, config: StorageConfig, cache_manager: CacheManagerProtocol):
        """Initialize StateManager with configuration.
        
        Args:
            config: Storage configuration
            cache_manager: Cache manager for state storage
        """
        logger.info("Initializing StateManager")
        self.config = config
        self.cache = cache_manager
        self.logger = logging.getLogger(__name__)
        self._current_state: Optional[GameState] = None
        self._game_id: Optional[str] = None

    async def initialize(self) -> None:
        """Initialize state manager and generate game ID."""
        try:
            self._game_id = str(uuid.uuid4())
            self.config.game_id = self._game_id
            logger.info(f"Initialized state manager with game ID: {self._game_id}")
        except Exception as e:
            logger.error(f"Failed to initialize state manager: {e}")
            raise StateError(f"Failed to initialize state manager: {str(e)}")

    @property
    def game_id(self) -> str:
        """Get current game ID."""
        if not self._game_id:
            raise StateError("State manager not initialized")
        return self._game_id

    @property
    def current_state(self) -> Optional[GameState]:
        """Get current game state."""
        return self._current_state

    def _validate_format(self, state: GameState) -> bool:
        """Validate basic state format.
        
        Args:
            state: State to validate
            
        Returns:
            bool: True if format is valid
        """
        try:
            if not state:
                return False
                
            # Basic format validation
            if not isinstance(state.section_number, int):
                return False
                
            if state.section_number < 1:
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating state format: {e}")
            return False

    def _serialize_state(self, state: GameState) -> str:
        """Serialize state to JSON.
        
        Args:
            state: State to serialize
            
        Returns:
            str: JSON string
            
        Raises:
            StateError: If serialization fails
        """
        try:
            state_dict = state.model_dump()
            return json.dumps(state_dict, default=_json_serial)
        except Exception as e:
            logger.error(f"Error serializing state: {e}")
            raise StateError(f"Failed to serialize state: {str(e)}")

    def _deserialize_state(self, json_data: str) -> GameState:
        """Deserialize JSON to state.
        
        Args:
            json_data: JSON string to deserialize
            
        Returns:
            GameState: Deserialized state
            
        Raises:
            StateError: If deserialization fails
        """
        try:
            state_dict = json.loads(json_data)
            return GameState.model_validate(state_dict)
        except Exception as e:
            logger.error(f"Error deserializing state: {e}")
            raise StateError(f"Failed to deserialize state: {str(e)}")

    async def _persist_state(self, state: GameState) -> GameState:
        """Persist state to storage.
        
        Args:
            state: State to persist
            
        Returns:
            GameState: Persisted state
            
        Raises:
            StateError: If persistence fails
        """
        try:
            json_data = self._serialize_state(state)
            
            await self.cache.save_cached_content(
                key=f"section_{state.section_number}",
                namespace="state",
                data=json_data
            )
            
            self._current_state = state
            return state
            
        except Exception as e:
            logger.error(f"Error persisting state: {e}")
            raise StateError(f"Failed to persist state: {str(e)}")

    async def save_state(self, state: GameState) -> GameState:
        """Save state with basic validation.
        
        Args:
            state: State to save
            
        Returns:
            GameState: Saved state
            
        Raises:
            StateError: If validation or save fails
        """
        try:
            if not self._game_id:
                raise StateError("State manager not initialized")
                
            if not self._validate_format(state):
                raise StateError("Invalid state format")
                
            return await self._persist_state(state)
            
        except Exception as e:
            logger.error(f"Error saving state: {e}")
            raise StateError(f"Failed to save state: {str(e)}")

    async def load_state(self, section_number: int) -> Optional[GameState]:
        """Load state for a specific section.
        
        Args:
            section_number: Section number to load
            
        Returns:
            Optional[GameState]: Loaded state if exists
            
        Raises:
            StateError: If load fails
        """
        try:
            if not self._game_id:
                raise StateError("State manager not initialized")
                
            json_data = await self.cache.get_cached_content(
                key=f"section_{section_number}",
                namespace="state"
            )
            
            if not json_data:
                return None
                
            state = self._deserialize_state(json_data)
            self._current_state = state
            return state
            
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            raise StateError(f"Failed to load state: {str(e)}")

    async def get_current_state(self) -> Optional[GameState]:
        """Get current game state."""
        try:
            logger.debug("Getting current state")
            # Try to get from cache first
            state = await self.cache.get_cached_content(
                key="current_state",
                namespace="state"
            )
            if state:
                logger.debug("Found state in cache")
                return self._deserialize_state(state)
                
            # If not in cache, load from storage
            # TODO: Implement storage loading
            logger.debug("No current state found")
            return None
            
        except Exception as e:
            logger.error("Error getting current state: %s", str(e))
            raise StateError(f"Failed to get current state: {str(e)}")

    async def clear_state(self) -> None:
        """Clear current state."""
        self._current_state = None

    async def create_initial_state(
        self,
        session_id: str,
        **init_params: Dict[str, Any]
    ) -> GameState:
        """Create and return initial game state.
        
        Args:
            session_id: Unique session identifier
            **init_params: Additional initialization parameters
            
        Returns:
            GameState: Initial state
            
        Raises:
            StateError: If creation fails
        """
        try:
            if not self._game_id:
                await self.initialize()
                
            logger.info("Creating initial state for session '{}'", session_id)
            
            # Create initial state with section 1
            params = {
                'section_number': 1,
                'session_id': session_id,
                'last_update': self.get_current_timestamp(),
                **init_params
            }
            
            initial_state = GameState(**params)
            
            logger.debug("Initial state created: section={}, session={}",
                        initial_state.section_number, session_id)
            
            # Save initial state
            saved_state = await self.save_state(initial_state)
            self._current_state = saved_state
            
            return saved_state
            
        except Exception as e:
            logger.error("Failed to create initial state: {}", str(e), exc_info=True)
            raise StateError(f"Failed to create initial state: {str(e)}")

    async def create_error_state(self, error_message: str) -> GameState:
        """Create error state.
        
        Args:
            error_message: Error message
            
        Returns:
            GameState: Error state
            
        Raises:
            StateError: If creation fails
        """
        try:
            if not self._game_id:
                await self.initialize()
                
            error_state = GameState(
                section_number=self._current_state.section_number if self._current_state else 1,
                error=error_message
            )
            return await self.save_state(error_state)
            
        except Exception as e:
            logger.error(f"Error creating error state: {e}")
            raise StateError(f"Failed to create error state: {str(e)}")

    def get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format.
        
        Returns:
            str: Current timestamp in ISO format
        """
        return datetime.now().isoformat()
