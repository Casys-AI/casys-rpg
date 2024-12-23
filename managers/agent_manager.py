"""
Agent Manager Module
Handles high-level game coordination and user interactions.
"""

from typing import Optional, AsyncGenerator, Dict, Any
from models.game_state import GameState
from agents.factories.game_factory import GameFactory, GameAgents, GameManagers

from agents.protocols.story_graph_protocol import StoryGraphProtocol
from agents.protocols.narrator_agent_protocol import NarratorAgentProtocol
from agents.protocols.rules_agent_protocol import RulesAgentProtocol
from agents.protocols.decision_agent_protocol import DecisionAgentProtocol
from agents.protocols.trace_agent_protocol import TraceAgentProtocol
from managers.protocols.rules_manager_protocol import RulesManagerProtocol

from managers.protocols.state_manager_protocol import StateManagerProtocol
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
from managers.protocols.character_manager_protocol import CharacterManagerProtocol
from managers.protocols.trace_manager_protocol import TraceManagerProtocol
from managers.protocols.agent_manager_protocol import AgentManagerProtocol
from managers.protocols.decision_manager_protocol import DecisionManagerProtocol

from config.storage_config import StorageConfig

from agents.base_agent import BaseAgent
from managers.rules_manager import RulesManager

import logging

logger = logging.getLogger(__name__)

class AgentManager:
    """High-level coordinator for game interactions.
    Responsible for:
    1. Managing user interactions and requests
    2. Coordinating game state and progression
    3. Error handling and feedback
    4. Session management
    """
    
    def __init__(
        self,
        agents: 'GameAgents',
        managers: 'GameManagers'
    ) -> None:
        """Initialize AgentManager with game components.
        
        Args:
            agents: Container with all game agents
            managers: Container with all game managers
        """
        self._agents = agents
        self._managers = managers
        self.logger = logger
        self.story_graph = None  # Will be initialized in initialize()

    def get_agent(self, agent_type: str) -> BaseAgent:
        """Get or create an agent instance.
        
        Args:
            agent_type: Type of agent to get ('rules', 'narrator', etc.)
            
        Returns:
            BaseAgent: Instance of the requested agent type
        """
        agent_map = {
            'rules': self._agents.rules_agent,
            'narrator': self._agents.narrator_agent,
            'decision': self._agents.decision_agent,
            'trace': self._agents.trace_agent
        }
        return agent_map[agent_type]

    @property
    def narrator_agent(self) -> NarratorAgentProtocol:
        """Get the narrator agent instance."""
        return self.get_agent('narrator')

    @property
    def rules_agent(self) -> RulesAgentProtocol:
        """Get the rules agent instance."""
        return self.get_agent('rules')

    @property
    def decision_agent(self) -> DecisionAgentProtocol:
        """Get the decision agent instance."""
        return self.get_agent('decision')

    @property
    def trace_agent(self) -> TraceAgentProtocol:
        """Get the trace agent instance."""
        return self.get_agent('trace')

    async def initialize(self):
        """Initialize the agent manager.
        This should be called after construction to set up dependencies.
        """
        self.story_graph = self._configure_story_graph()
        await self.initialize_game()
        
    def _configure_story_graph(self) -> StoryGraphProtocol:
        """Configure the story graph with all dependencies.
        
        Returns:
            StoryGraphProtocol: Configured story graph instance
        """
        factory = GameFactory()
        
        return factory.create_story_graph(self._agents, self._managers)

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
        return await self._managers.state_manager.get_current_state()

    async def subscribe_to_updates(self) -> AsyncGenerator[GameState, None]:
        """Stream les mises à jour du jeu en temps réel."""
        try:
            async for state in self.story_graph.stream_game_state():
                yield GameState.model_validate(state)
        except Exception as e:
            self.logger.error(f"Error streaming game state: {e}")
            error_state = await self._managers.state_manager.create_error_state(str(e))
            yield error_state

    async def navigate_to_section(self, section_number: int) -> GameState:
        """
        Process a user's request to move to a specific section.
        
        Args:
            section_number: The section number requested by the user
            
        Returns:
            GameState: Updated game state after processing the section
        """
        try:
            return await self.story_graph.navigate_to_section(section_number)
        except Exception as e:
            self.logger.error(f"Error navigating to section {section_number}: {e}")
            return await self._managers.state_manager.create_error_state(str(e))

    async def submit_response(self, response: str) -> GameState:
        """
        Process a user's response or decision.
        
        Args:
            response: The user's input or decision
            
        Returns:
            GameState: Updated game state after processing the response
        """
        try:
            return await self.story_graph.process_user_input(response)
        except Exception as e:
            self.logger.error(f"Error processing user response: {e}")
            return await self._managers.state_manager.create_error_state(str(e))

    async def perform_action(self, action: Dict[str, Any]) -> GameState:
        """
        Process a user's game action.
        
        Args:
            action: Dictionary containing action details
            
        Returns:
            GameState: Updated game state after processing the action
        """
        try:
            current_state = await self.get_state()
            return await self.story_graph.process_action(action, current_state)
        except Exception as e:
            self.logger.error(f"Error processing user action: {e}")
            return await self.create_error_response(str(e))

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
            return await self.story_graph.process_user_input(user_response)
        except Exception as e:
            self.logger.error(f"Error handling user decision: {str(e)}")
            return await self.create_error_response(str(e))

    async def process_section(self, section_number: int) -> GameState:
        """
        Traite une nouvelle section du jeu.
        
        Args:
            section_number: Numéro de la section à traiter
            
        Returns:
            GameState: État après le traitement de la section
        """
        try:
            return await self.story_graph.navigate_to_section(section_number)
        except Exception as e:
            self.logger.error(f"Error processing section {section_number}: {str(e)}")
            return await self.create_error_response(str(e))

    async def process_section_with_updates(self, section_number: int) -> AsyncGenerator[GameState, None]:
        """
        Traite une section en streamant les mises à jour d'état.
        
        Args:
            section_number: Numéro de la section à traiter
            
        Yields:
            GameState: États intermédiaires pendant le traitement
        """
        try:
            # Initialiser le story graph si nécessaire
            if not self.story_graph:
                await self.initialize()
                
            # Obtenir l'état initial
            initial_state = await self._managers.state_manager.get_state() or {}
            
            # Streamer les mises à jour via story graph
            async for state in self.story_graph.stream_game_state():
                yield state
                
        except Exception as e:
            self.logger.error(f"Error processing section with updates: {str(e)}")
            yield await self.create_error_response(str(e))

    async def create_error_response(self, error: str) -> GameState:
        """
        Create an error state response.
        
        Args:
            error: Error message
            
        Returns:
            GameState: Error state
        """
        return await self._managers.state_manager.create_error_state(error)

    async def get_user_feedback(self) -> str:
        """
        Get feedback about the current game state.
        
        Returns:
            str: Feedback message
        """
        try:
            current_state = await self.get_state()
            return await self._managers.trace_manager.get_feedback(current_state)
        except Exception as e:
            logger.error(f"Error getting user feedback: {e}")
            return f"Error getting feedback: {e}"

# Add runtime type checking for protocol
AgentManagerProtocol.register(AgentManager)
