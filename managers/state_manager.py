"""
State Manager Module
Manages game state persistence and validation.
"""

from typing import Dict, Optional, Any, List
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
from models.character_model import CharacterModel, CharacterStats  # Import CharacterModel and CharacterStats

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

    async def initialize(self, game_id: Optional[str] = None) -> None:
        """Initialize state manager and generate game ID.
        
        Args:
            game_id: Optional game ID to use. If not provided, a new one will be generated.
        """
        logger.info("Initializing StateManager")
        self._game_id = game_id if game_id else str(uuid.uuid4())
        logger.debug("Generated game ID: {}", self._game_id)
        self.config.game_id = self._game_id
        await self.cache.update_game_id(self._game_id)
        logger.info(f"Initialized state manager with game ID: {self._game_id}")

    @property
    def game_id(self) -> str:
        """Get current game ID."""
        if not self._game_id:
            raise StateError("State manager not initialized")
        return self._game_id

    async def get_game_id(self) -> Optional[str]:
        """Get current game ID."""
        return self._game_id

    @staticmethod
    def generate_session_id() -> str:
        """Generate a unique session ID."""
        return str(uuid.uuid4())

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
            # Préserver explicitement les IDs
            state_dict["session_id"] = state.session_id
            state_dict["game_id"] = self._game_id
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
            if not self._game_id:
                raise StateError("No game ID set for persistence")

            json_data = self._serialize_state(state)
            
            # Sauvegarder l'état courant
            await self.cache.save_cached_data(
                key=f"game_{self._game_id}_current",
                namespace="state",
                data=json_data
            )
            
            # Sauvegarder aussi par section pour l'historique
            await self.cache.save_cached_data(
                key=f"game_{self._game_id}_section_{state.section_number}",
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
                
            json_data = await self.cache.get_cached_data(
                key=f"game_{self._game_id}_section_{section_number}",
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

    async def get_section_history(self) -> List[int]:
        """Get list of available sections for current game."""
        try:
            if not self._game_id:
                raise StateError("State manager not initialized")
                
            # Récupérer toutes les sections sauvegardées pour ce game_id
            sections = []
            pattern = f"game_{self._game_id}_section_*"
            keys = await self.cache.list_keys(namespace="state", pattern=pattern)
            
            for key in keys:
                # Extraire le numéro de section de la clé
                section = int(key.split('_')[-1])
                sections.append(section)
                
            return sorted(sections)
            
        except Exception as e:
            logger.error(f"Error getting section history: {e}")
            raise StateError(f"Failed to get section history: {str(e)}")

    async def get_current_state(self) -> Optional[GameState]:
        """Get current game state."""
        return self._current_state

    async def clear_state(self) -> None:
        """Clear current game state and cache."""
        logger.info("Clearing game state")
        try:
            # Nettoyer l'état en mémoire
            self._current_state = None
            self._game_id = None
            
            # Nettoyer le cache
            if self.cache:
                await self.cache.clear()
                
            logger.info("Game state cleared successfully")
            
        except Exception as e:
            logger.error(f"Error clearing game state: {e}")
            raise StateError(f"Failed to clear game state: {str(e)}")

    async def switch_game(self, new_game_id: str) -> None:
        """Switch to a different game.
        
        Args:
            new_game_id: ID of the game to switch to
            
        Raises:
            StateError: If switch fails
        """
        try:
            # Sauvegarder l'état actuel si nécessaire
            if self._current_state:
                await self._persist_state(self._current_state)
                
            # Changer de partie
            old_game_id = self._game_id
            await self.initialize(new_game_id)
            
            logger.info(f"Switched from game {old_game_id} to {new_game_id}")
            
        except Exception as e:
            logger.error(f"Error switching game: {e}")
            raise StateError(f"Failed to switch game: {str(e)}")

    async def create_initial_state(self, **init_params: Dict[str, Any]) -> GameState:
        """Create and return the initial game state.

        Args:
            **init_params: Additional parameters for initializing the state

        Returns:
            GameState: The initial state
        """
        try:
            if not self._game_id:
                await self.initialize()

            # Générer automatiquement un session_id via la méthode statique
            session_id = self.generate_session_id()
            logger.info(f"Creating initial state with session_id: {session_id}")

            # Créer et sauvegarder le personnage initial
            initial_character = CharacterModel(
                stats=CharacterStats(
                    endurance=20,
                    chance=20,
                    skill=20
                )
            )
            await self.cache.save_cached_data(
                key="current",
                namespace="characters",
                data=initial_character.model_dump()
            )

            # Définir les paramètres nécessaires pour GameState
            params = {
                'section_number': 1,
                'session_id': session_id,
                'game_id': self._game_id, 
                'last_update': self.get_current_timestamp(),
                'character_id': "current",
                **init_params  #useful?
            }

            # Créer l'état initial
            logger.debug(f"Parameters for initial GameState: {params}")
            initial_state = GameState(**params)

            # Sauvegarder l'état initial
            saved_state = await self.save_state(initial_state)
            self._current_state = saved_state

            return saved_state

        except Exception as e:
            logger.error(f"Failed to create initial state: {e}", exc_info=True)
            raise StateError(f"Failed to create initial state: {e}")

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
                
            # Générer un nouveau session_id si pas d'état courant
            session_id = (self._current_state.session_id 
                        if self._current_state 
                        else await self.generate_session_id())
                
            error_state = GameState(
                session_id=session_id,
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
