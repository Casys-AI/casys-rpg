"""
Agent Manager Module
Handles high-level game coordination and user interactions.
"""

from typing import Dict, Optional, Any, AsyncGenerator
from models.game_state import GameState
from agents.story_graph import StoryGraph
from managers.state_manager import StateManager
from managers.cache_manager import CacheManager
from managers.character_manager import CharacterManager
from managers.trace_manager import TraceManager
from config.game_config import GameConfig
from models.agent_manager_protocol import AgentManagerProtocol
import logging

logger = logging.getLogger(__name__)

class AgentManager(AgentManagerProtocol):
    """High-level coordinator for game interactions.
    Responsible for:
    1. Managing user interactions and requests
    2. Coordinating game state and progression
    3. Error handling and feedback
    4. Session management
    """
    
    def __init__(self, game_config: GameConfig):
        """Initialize AgentManager with game configuration.
        
        Args:
            game_config: Global game configuration
        """
        self.config = game_config
        self.cache_manager = CacheManager(game_config)
        self.state_manager = StateManager(game_config)
        self.character_manager = CharacterManager(game_config)
        self.trace_manager = TraceManager(game_config)
        self.story_graph = None
        
    def initialize(self):
        """Initialize AgentManager and configure components."""
        self.story_graph = self._configure_story_graph()
        
    def _configure_story_graph(self) -> StoryGraph:
        """Configure the story graph with managers.
        
        Returns:
            StoryGraph: Configured story graph instance
        """
        return StoryGraph(
            cache_manager=self.cache_manager,
            state_manager=self.state_manager,
            character_manager=self.character_manager,
            trace_manager=self.trace_manager
        )

    async def initialize_game(self) -> None:
        """
        Start a new game session.
        This prepares the game state and initializes all components.
        Can be called multiple times to start new sessions.
        """
        try:
            logger.info("Starting new game session...")
            await self.story_graph.start_session()
            logger.info("Game session started successfully")
        except Exception as e:
            logger.error(f"Failed to start game session: {e}")
            raise

    async def get_state(self) -> GameState:
        """Get the current state of the game."""
        return await self.state_manager.get_current_state()

    async def subscribe_to_updates(self) -> AsyncGenerator[GameState, None]:
        """Stream les mises à jour du jeu en temps réel."""
        try:
            async for state in self.story_graph.stream_game_state():
                # Convertir en GameState pour validation
                game_state = GameState(**state)
                # Mettre à jour le state manager
                await self.state_manager.update_state(game_state)
                yield game_state
        except Exception as e:
            self.logger.error(f"Error streaming game updates: {e}")
            error_state = await self.state_manager.create_error_state(str(e))
            yield GameState(**error_state)

    async def navigate_to_section(self, section_number: int) -> GameState:
        """
        Process a user's request to move to a specific section.
        
        Args:
            section_number: The section number requested by the user
            
        Returns:
            GameState: Updated game state after processing the section
        """
        try:
            return await self.story_graph.process_game_section(section_number)
        except Exception as e:
            logger.error(f"Error processing section {section_number}: {e}")
            return self.create_error_response(str(e))

    async def submit_response(self, response: str) -> GameState:
        """
        Process a user's response or decision.
        
        Args:
            response: The user's input or decision
            
        Returns:
            GameState: Updated game state after processing the response
        """
        try:
            current_state = await self.get_current_game_state()
            return await self.story_graph.process_response(response, current_state)
        except Exception as e:
            logger.error(f"Error processing user response: {e}")
            return self.create_error_response(str(e))

    async def perform_action(self, action: Dict[str, Any]) -> GameState:
        """
        Process a user's game action.
        
        Args:
            action: Dictionary containing action details
            
        Returns:
            GameState: Updated game state after processing the action
        """
        try:
            current_state = await self.get_current_game_state()
            return await self.story_graph.process_action(action, current_state)
        except Exception as e:
            logger.error(f"Error processing user action: {e}")
            return self.create_error_response(str(e))

    async def should_continue(self, state: GameState) -> bool:
        """
        Vérifie si le jeu doit continuer.
        
        Args:
            state: État actuel du jeu
            
        Returns:
            bool: True si le jeu doit continuer
        """
        try:
            # Stop si erreur
            if state.error:
                self.logger.info(f"Game stopped due to error: {state.error}")
                return False
                
            # Stop si fin de jeu
            if getattr(state, 'end_game', False):
                self.logger.info("Game ended normally")
                return False
                
            # Stop si pas de section valide
            if not state.section_number:
                self.logger.error("No valid section number")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking game continuation: {str(e)}")
            return False

    async def handle_decision(self, user_response: str) -> GameState:
        """
        Gère une décision utilisateur.
        
        Args:
            user_response: Réponse de l'utilisateur
            
        Returns:
            GameState: Nouvel état après la décision
        """
        try:
            # Récupérer l'état actuel
            current_state = await self.state_manager.get_state()
            if not current_state:
                raise ValueError("No current game state")
                
            # Créer la mise à jour
            update = {
                "user_response": user_response,
                "decision": {"type": "user_input", "value": user_response}
            }
            
            # Mettre à jour via story graph
            updated_state = await self.story_graph._process_workflow({
                **current_state,
                **update
            })
            
            return GameState(**updated_state)
            
        except Exception as e:
            self.logger.error(f"Error handling user decision: {str(e)}")
            error_state = await self.state_manager.create_error_state(str(e))
            return GameState(**error_state)

    async def process_section(self, section_number: int) -> GameState:
        """
        Traite une nouvelle section du jeu.
        
        Args:
            section_number: Numéro de la section à traiter
            
        Returns:
            GameState: État après le traitement de la section
        """
        try:
            # Initialiser l'état si nécessaire
            current_state = await self.state_manager.get_state()
            if not current_state:
                current_state = {}
                
            # Ajouter le numéro de section
            update = {
                **current_state,
                "section_number": section_number
            }
            
            # Traiter via story graph
            processed_state = await self.story_graph._process_workflow(update)
            return GameState(**processed_state)
            
        except Exception as e:
            self.logger.error(f"Error processing section {section_number}: {str(e)}")
            error_state = await self.state_manager.create_error_state(str(e))
            return GameState(**error_state)

    async def create_error_response(self, error: str) -> GameState:
        """
        Create an error state response.
        
        Args:
            error: Error message
            
        Returns:
            GameState: Error state
        """
        return await self.state_manager.create_error_state(error)

    async def get_user_feedback(self) -> str:
        """
        Get feedback about the current game state.
        
        Returns:
            str: Feedback message
        """
        try:
            current_state = await self.get_state()
            return await self.trace_manager.get_feedback(current_state)
        except Exception as e:
            logger.error(f"Error getting user feedback: {e}")
            return f"Error getting feedback: {e}"
