"""
State Manager Module
Manages game state persistence and validation.
"""

from typing import Dict, Optional, Any, List, Union
from pydantic import BaseModel, ValidationError
import json
import logging
from datetime import datetime
from pathlib import Path
import uuid

from models.game_state import GameState
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
    """Manages game state persistence and validation."""
    
    def __init__(self, config: StorageConfig, cache_manager: CacheManagerProtocol):
        """Initialize StateManager with configuration."""
        self.config = config
        self.cache = cache_manager
        self.logger = logging.getLogger(__name__)
        self._current_state: Optional[GameState] = None
        self._state_history: List[GameState] = []
        self._game_id: Optional[str] = None

    async def initialize(self) -> None:
        """Initialize the state manager and generate game_id."""
        try:
            self._game_id = str(uuid.uuid4())
            self.config.game_id = self._game_id
            self.logger.info(f"Initialized state manager with game ID: {self._game_id}")
        except Exception as e:
            self.logger.error(f"Failed to initialize state manager: {e}")
            raise StateError(f"Failed to initialize state manager: {str(e)}")

    @property
    def game_id(self) -> str:
        """Get current game ID."""
        if not self._game_id:
            raise StateError("State manager not initialized. Call initialize() first.")
        return self._game_id

    @property
    def current_state(self) -> Optional[GameState]:
        """Get current game state."""
        return self._current_state

    @property
    def state_history(self) -> List[GameState]:
        """Get state history."""
        return self._state_history.copy()

    def _serialize_state(self, state: GameState) -> str:
        """Serialize state to JSON."""
        try:
            state_dict = state.model_dump()
            return json.dumps(state_dict, default=_json_serial)
        except Exception as e:
            self.logger.error(f"Error serializing state: {e}")
            raise StateError(f"Failed to serialize state: {str(e)}")

    def _deserialize_state(self, json_data: str) -> GameState:
        """Deserialize JSON to state."""
        try:
            state_dict = json.loads(json_data)
            return GameState.model_validate(state_dict)
        except Exception as e:
            self.logger.error(f"Error deserializing state: {e}")
            raise StateError(f"Failed to deserialize state: {str(e)}")

    async def save_state(self, state: GameState) -> GameState:
        """Save current state."""
        try:
            if not self._game_id:
                raise StateError("State manager not initialized. Call initialize() first.")
                
            json_data = self._serialize_state(state)
            
            await self.cache.save_cached_content(
                key=f"section_{state.section_number}",
                namespace="state",
                data=json_data
            )
            
            self._current_state = state
            if not self._state_history or self._state_history[-1] != state:
                self._state_history.append(state)
                
            return state
            
        except Exception as e:
            self.logger.error(f"Error saving state: {e}")
            raise StateError(f"Failed to save state: {str(e)}")

    async def load_state(self, section_number: int) -> Optional[GameState]:
        """Load state for a specific section."""
        try:
            if not self._game_id:
                raise StateError("State manager not initialized. Call initialize() first.")
                
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
            self.logger.error(f"Error loading state: {e}")
            raise StateError(f"Failed to load state: {str(e)}")

    def get_current_state(self) -> Optional[GameState]:
        """Get current game state."""
        return self._current_state

    def get_state_history(self) -> List[GameState]:
        """Get state history."""
        return self._state_history.copy()

    async def clear_state(self) -> None:
        """Clear current state."""
        self._current_state = None
        self._state_history.clear()

    def validate_state(self, state: GameState) -> bool:
        """Validate game state."""
        try:
            # Basic validation
            if not state:
                return False
            if state.section_number < 1:
                return False
            return True
        except Exception as e:
            self.logger.error(f"Error validating state: {e}")
            return False

    async def create_initial_state(self) -> GameState:
        """Create and return an initial game state."""
        if not self._game_id:
            await self.initialize()
        initial_state = GameState(section_number=1)
        return await self.save_state(initial_state)

    async def create_error_state(self, error_message: str) -> GameState:
        """Create an error state with the given message."""
        if not self._game_id:
            await self.initialize()
        error_state = GameState(
            section_number=self._current_state.section_number if self._current_state else 1,
            error=error_message
        )
        return await self.save_state(error_state)

    async def update_state(self, new_state: Dict | GameState) -> bool:
        """Update current game state with validation."""
        try:
            if isinstance(new_state, dict):
                state = GameState.model_validate(new_state)
            else:
                state = new_state

            if not self.validate_state(state):
                return False

            await self.save_state(state)
            return True
        except Exception as e:
            self.logger.error(f"Error updating state: {e}")
            return False
