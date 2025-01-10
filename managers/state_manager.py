"""
State Manager Module
Manages game state persistence and validation.
"""

from typing import Dict, Optional, Any, List, Union
from pydantic import BaseModel, ValidationError
import json
import logging
from datetime import datetime
import uuid
from loguru import logger

from models.game_state import GameState
from config.storage_config import StorageConfig
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
from managers.protocols.state_manager_protocol import StateManagerProtocol
from managers.protocols.character_manager_protocol import CharacterManagerProtocol
from models.errors_model import StateError
from models.character_model import CharacterModel, CharacterStats
from agents.factories.model_factory import ModelFactory

def _json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

class StateManager(StateManagerProtocol):
    """Manages game state persistence and basic validation."""
    
    def __init__(
        self, 
        config: StorageConfig, 
        cache_manager: CacheManagerProtocol,
        character_manager: CharacterManagerProtocol
    ):
        """Initialize StateManager with configuration.
        
        Args:
            config: Storage configuration
            cache_manager: Cache manager for state storage
            character_manager: Character manager for character operations
        """
        logger.info("Initializing StateManager")
        self.config = config
        self.cache = cache_manager
        self.character_manager = character_manager
        self._current_state: Optional[GameState] = None
        self._game_id: Optional[str] = None
        self._session_id: Optional[str] = None
        logger.debug("StateManager initialized with config: {}", config)

    async def initialize(self) -> None:
        """Initialize state manager.
        Sets up any necessary resources and state.
        """
        logger.info("Initializing state resources")
        
        # Générer les IDs nécessaires
        if not self._game_id:
            self._game_id = str(uuid.uuid4())
            logger.debug("Generated new game ID: {}", self._game_id)
        
        if not self._session_id:
            self._session_id = str(uuid.uuid4())
            logger.debug("Generated new session ID: {}", self._session_id)
            
        # Configurer le cache
        self.config.game_id = self._game_id
        await self.cache.update_game_id(self._game_id)
        logger.info("State manager initialized with game ID: {}, session ID: {}", 
                   self._game_id, self._session_id)

    @property
    def game_id(self) -> Optional[str]:
        """Get current game ID."""
        return self._game_id

    async def get_game_id(self) -> Optional[str]:
        """Get current game ID."""
        return self._game_id

    @property
    def session_id(self) -> Optional[str]:
        """Get current session ID."""
        return self._session_id

    async def get_session_id(self) -> Optional[str]:
        """Get current session ID."""
        return self._session_id

    @property
    def current_state(self) -> Optional[GameState]:
        """Get current game state."""
        return self._current_state

    async def get_current_state(self) -> Optional[GameState]:
        """Get current game state."""
        return self._current_state

    @property
    def current_timestamp(self) -> str:
        """Get current timestamp in ISO format.
        
        Returns:
            str: Current timestamp in ISO format
        """
        return datetime.utcnow().isoformat()

    def _truncate_content(self, content: Optional[str], max_length: int = 100) -> str:
        """Tronque le contenu pour les logs.
        
        Args:
            content: Contenu à tronquer
            max_length: Longueur maximale
            
        Returns:
            str: Contenu tronqué
        """
        if not content:
            return "None"
        return f"{content[:max_length]}..." if len(content) > max_length else content

    def _validate_format(self, state: GameState) -> bool: #should be in a model or game state
        """Validate state format.
        
        Args:
            state: State to validate
            
        Returns:
            bool: True if format is valid
        """
        try:
            logger.debug("Validating format for state, narrative content: {}", 
                        self._truncate_content(state.narrative.content if state.narrative else None))
            
            # Vérifier les champs requis
            if not state.session_id:
                logger.error("Missing session_id")
                return False
                
            # Vérifier la cohérence des données
            if state.narrative:
                logger.debug("Checking narrative content: {}", 
                           self._truncate_content(state.narrative.content))
                if state.narrative.section_number != state.section_number:
                    logger.error("Narrative section number mismatch: {} != {}", 
                               state.narrative.section_number, state.section_number)
                    return False
                    
            logger.debug("Format validation successful, narrative content: {}", 
                        self._truncate_content(state.narrative.content if state.narrative else None))
            return True
            
        except Exception as e:
            logger.error("Error validating format: {}", str(e))
            return False

    async def validate_state( #should be in game state, not in a business file
        self, 
        state_data: Union[Dict[str, Any], GameState]
    ) -> GameState:
        """Validate and convert state data to GameState.
        
        Args:
            state_data: State data to validate
            
        Returns:
            GameState: Validated state instance
            
        Raises:
            StateError: If validation fails
        """
        try:
            logger.debug("Validating state data: {}", state_data)
            
            if isinstance(state_data, GameState):
                logger.debug("Input is GameState, narrative content: {}", 
                           self._truncate_content(state_data.narrative.content if state_data.narrative else None))
                if not self._validate_format(state_data):
                    raise StateError("Invalid state format")
                return state_data
                
            logger.debug("Input is Dict, narrative content: {}", 
                        self._truncate_content(state_data.get('narrative', {}).get('content') if state_data.get('narrative') else None))
            state = GameState(**state_data)
            logger.debug("Created GameState, narrative content: {}", 
                        self._truncate_content(state.narrative.content if state.narrative else None))
            
            if not self._validate_format(state):
                raise StateError("Invalid state format")
                
            logger.debug("State format validated, narrative content: {}", 
                        self._truncate_content(state.narrative.content if state.narrative else None))
            return state
            
        except Exception as e:
            logger.error("Error validating state: {}", str(e))
            raise StateError(f"Failed to validate state: {str(e)}")

    async def create_initial_state(
            self, 
            input_data: Optional[Union[Dict[str, Any], GameState]] = None
        ) -> GameState:
        """Create and initialize a new game state.
        
        This method handles:
        1. Extraction des données à préserver de l'input
        2. Nettoyage de l'état existant
        3. Création d'un nouvel état avec les données préservées
        4. Validation et sauvegarde
        
        Args:
            input_data: Optional initial state data to merge
            
        Returns:
            GameState: The newly created and initialized state
            
        Raises:
            StateError: If state creation or validation fails
        """
        try:
            logger.info("Creating initial state")
            
            # 1. S'assurer que le state manager est initialisé
            if not self._game_id:
                await self.initialize()
            
            # 2. Extraire les données à préserver
            preserved_data = self._extract_preserved_data(input_data)
            logger.debug("Preserved data extracted: {}", preserved_data)
            
            # 3. Nettoyer l'état existant
            await self.clear_model_nodes()
            logger.debug("Existing state cleared")
            
            # 4. Créer le nouvel état avec les données préservées
            initial_state = ModelFactory.create_game_state(
                session_id=preserved_data["session_id"],
                game_id=preserved_data["game_id"],
                section_number=preserved_data["section_number"],
                character=preserved_data["character"],
                timestamp=self.current_timestamp
            )
            logger.debug("New state created with preserved data")
            
            # 5. Valider et sauvegarder
            validated_state = await self.validate_state(initial_state)
            saved_state = await self.save_state(validated_state)
            
            self._current_state = saved_state
            return saved_state

        except Exception as e:
            error_msg = f"Failed to create initial state: {str(e)}"
            logger.error(error_msg)
            raise StateError(error_msg) from e
            
    def _extract_preserved_data(
        self,
        input_data: Optional[Union[Dict[str, Any], GameState]] = None
    ) -> Dict[str, Any]:
        """Extrait les données à préserver de l'input.
        
        Args:
            input_data: Données d'entrée (GameState ou dict)
            
        Returns:
            Dict[str, Any]: Données préservées avec valeurs par défaut si nécessaire
        """
        # Initialiser avec les valeurs par défaut
        preserved_data = {
            "session_id": self._session_id,
            "game_id": self._game_id,
            "section_number": 1,
            "character": None
        }
        
        if isinstance(input_data, GameState):
            # Préserver les IDs
            preserved_data["session_id"] = input_data.session_id
            preserved_data["game_id"] = input_data.game_id
            
            # Utiliser next_section du DecisionModel si disponible
            if input_data.decision and input_data.decision.next_section:
                preserved_data["section_number"] = input_data.decision.next_section
            else:
                preserved_data["section_number"] = input_data.section_number
                
            preserved_data["character"] = input_data.character
            
        elif isinstance(input_data, dict):
            # Préserver les IDs s'ils existent
            if "session_id" in input_data:
                preserved_data["session_id"] = input_data["session_id"]
            if "game_id" in input_data:
                preserved_data["game_id"] = input_data["game_id"]
                
            # Utiliser next_section du DecisionModel si disponible
            decision = input_data.get("decision", {})
            if isinstance(decision, dict) and "next_section" in decision:
                preserved_data["section_number"] = decision["next_section"]
            elif "section_number" in input_data:
                preserved_data["section_number"] = input_data["section_number"]
                
            if "character" in input_data:
                preserved_data["character"] = input_data["character"]
                
        # Créer un nouveau character si nécessaire
        if not preserved_data["character"]:
            preserved_data["character"] = CharacterModel(
                id="current",
                stats=CharacterStats(
                    endurance=20,
                    chance=20,
                    skill=20
                )
            )
            
        return preserved_data

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
        try:
            logger.info("Creating error state")
            base_state = current_state or self._current_state
            
            if base_state:
                # Utiliser la méthode de GameState
                error_state = GameState.create_error_state(
                    error_message=error_message,
                    section_number=base_state.section_number,
                    session_id=base_state.session_id,
                    game_id=base_state.game_id,
                    current_state=base_state
                )
            else:
                # Créer un état minimal avec ModelFactory
                error_state = ModelFactory.create_game_state(
                    session_id=self._session_id,
                    game_id=self._game_id,
                    error=error_message,
                    timestamp=self.current_timestamp
                )
            
            saved_state = await self.save_state(error_state)
            logger.debug("Created error state: {}", saved_state)
            return saved_state
            
        except Exception as e:
            # En cas d'erreur lors de la création de l'état d'erreur,
            # créer un état minimal avec ModelFactory
            logger.error("Failed to create error state: {}", str(e))
            return ModelFactory.create_game_state(
                session_id=self._session_id,
                game_id=self._game_id,
                error=f"{error_message} (Error state creation failed: {str(e)})",
                timestamp=self.current_timestamp
            )

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
            logger.debug("Saving state, input narrative content: {}", 
                        self._truncate_content(state.narrative.content if state.narrative else None))
            
            if not self._game_id:
                raise StateError("State manager not initialized")
                
            # Valider l'état
            validated_state = await self.validate_state(state)
            logger.debug("State validated, narrative content: {}", 
                        self._truncate_content(validated_state.narrative.content if validated_state.narrative else None))
            
            # Sérialiser
            json_data = validated_state.model_dump()
            logger.debug("State serialized, narrative content in json: {}", 
                        self._truncate_content(json_data.get('narrative', {}).get('content') if json_data.get('narrative') else None))
            
            # Sauvegarder l'état courant
            await self.cache.save_cached_data(
                key=f"game_{self._game_id}_current",
                namespace="state",
                data=json_data
            )
            logger.debug("Current state saved to cache")
            
            # Sauvegarder aussi par section pour l'historique
            await self.cache.save_cached_data(
                key=f"game_{self._game_id}_section_{state.section_number}",
                namespace="state",
                data=json_data
            )
            logger.debug("Section state saved to cache")
            
            self._current_state = validated_state
            logger.debug("Current state updated, final narrative content: {}", 
                        self._truncate_content(self._current_state.narrative.content if self._current_state.narrative else None))
            
            return validated_state
            
        except Exception as e:
            logger.error("Error saving state: {}", str(e))
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
                
            state = GameState(**json.loads(json_data))
            self._current_state = state
            return state
            
        except Exception as e:
            logger.error("Error loading state: {}", str(e))
            raise StateError(f"Failed to load state: {str(e)}")

    async def get_section_history(self) -> List[int]: #no test
        """Get list of all saved section numbers for current game."""
        try:
            # Récupérer toutes les sections sauvegardées pour ce game_id
            sections = []
            pattern = f"game_{self._game_id}_section_*"
            keys = await self.cache.list_keys(namespace="state", pattern=pattern)
            
            for key in keys:
                # Extraire le numéro de section de la clé
                section = int(key.split("_")[-1])
                sections.append(section)
                
            return sorted(sections)
            
        except Exception as e:
            logger.error("Error getting section history: {}", str(e))
            raise StateError(f"Failed to get section history: {str(e)}")

    async def clear_state(self) -> None: #no test and we dont want to clear the persistance, it's persostenance, not cache
        """Clear current state and cache."""
        try:
            logger.info("Clearing game state")
            self._current_state = None
            self._game_id = None
            
            # Nettoyer le cache
            if self.cache:
                await self.cache.clear()
                
            logger.info("Game state cleared successfully")
            
        except Exception as e:
            logger.error("Error clearing state: {}", str(e))
            raise StateError(f"Failed to clear state: {str(e)}")

    async def switch_game(self, new_game_id: str) -> None: #no test
        """Switch to a different game.
        
        Args:
            new_game_id: ID of the game to switch to
            
        Raises:
            StateError: If switch fails
        """
        try:
            logger.info("Switching to game: {}", new_game_id)
            self._game_id = new_game_id
            self.config.game_id = new_game_id
            await self.cache.update_game_id(new_game_id)
            await self.initialize()  # Réinitialiser avec le nouveau game_id
            self._current_state = None  # Reset current state
            logger.info("Switched to game: {}", new_game_id)
            
        except Exception as e:
            error_msg = f"Failed to switch game: {str(e)}"
            logger.error(error_msg)
            raise StateError(error_msg) from e

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
                raise StateError("State manager not initialized")
            
            logger.debug("Persisting state, narrative content: {}", 
                        self._truncate_content(state.narrative.content if state.narrative else None))
            
            # Sérialiser
            json_data = state.model_dump()
            logger.debug("State serialized, narrative content in json: {}", 
                        self._truncate_content(json_data.get('narrative', {}).get('content') if json_data.get('narrative') else None))
            
            # Sauvegarder l'état courant
            await self.cache.save_cached_data(
                key=f"game_{self._game_id}_current",
                namespace="state",
                data=json_data
            )
            logger.debug("Current state saved to cache")
            
            # Sauvegarder aussi par section pour l'historique
            await self.cache.save_cached_data(
                key=f"game_{self._game_id}_section_{state.section_number}",
                namespace="state",
                data=json_data
            )
            logger.debug("Section state saved to cache")
            
            return state
            
        except Exception as e:
            error_msg = f"Failed to persist state: {str(e)}"
            logger.error(error_msg)
            raise StateError(error_msg) from e

    async def clear_model_nodes(self) -> None:
        """Clear all model nodes in the current state.
        This ensures that old model instances are properly destroyed
        before creating new ones.
        """
        try:
            logger.info("Clearing model nodes")
            if self._current_state:
                # Créer un nouvel état vide qui préserve session_id, game_id et section_number
                self._current_state = GameState.create_empty_state(
                    session_id=self._current_state.session_id,
                    game_id=self._current_state.game_id,
                    section_number=self._current_state.section_number
                )
                
            # Force garbage collection
            import gc
            gc.collect()
            
            logger.debug("Model nodes cleared")
            
        except Exception as e:
            logger.error(f"Error clearing model nodes: {e}")
            # Non-blocking error - just log it
