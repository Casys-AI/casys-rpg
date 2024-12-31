"""
Agent Manager implementation.
"""

from typing import (
    Any, Optional, Dict, List, Union, Type, TypeVar, Generic)
from loguru import logger
from fastapi import Depends
from langgraph.types import Command
from langgraph.errors import GraphInterrupt

from managers.protocols.agent_manager_protocol import AgentManagerProtocol
from managers.protocols.state_manager_protocol import StateManagerProtocol
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
from managers.protocols.character_manager_protocol import CharacterManagerProtocol
from managers.protocols.trace_manager_protocol import TraceManagerProtocol
from managers.protocols.decision_manager_protocol import DecisionManagerProtocol
from managers.protocols.rules_manager_protocol import RulesManagerProtocol
from managers.protocols.narrator_manager_protocol import NarratorManagerProtocol
from managers.protocols.workflow_manager_protocol import WorkflowManagerProtocol

from agents.protocols.story_graph_protocol import StoryGraphProtocol
from agents.protocols.narrator_agent_protocol import NarratorAgentProtocol
from agents.protocols.rules_agent_protocol import RulesAgentProtocol
from agents.protocols.decision_agent_protocol import DecisionAgentProtocol
from agents.protocols.trace_agent_protocol import TraceAgentProtocol
from agents.protocols.base_agent_protocol import BaseAgentProtocol

from agents.factories.game_factory import GameFactory
from models.types.agent_types import GameAgents
from models.types.manager_types import GameManagers
from config.agents.agent_config_base import AgentConfigBase

from models.game_state import GameState
from models.errors_model import GameError

# Type alias for manager protocols
ManagerProtocols = Union[
    WorkflowManagerProtocol,
    StateManagerProtocol,
    CacheManagerProtocol,
    CharacterManagerProtocol,
    TraceManagerProtocol,
    RulesManagerProtocol,
    DecisionManagerProtocol,
    NarratorManagerProtocol
]

# Type alias for agent protocols
AgentProtocols = Union[
    NarratorAgentProtocol,
    RulesAgentProtocol,
    DecisionAgentProtocol,
    TraceAgentProtocol
]

class AgentManager(AgentManagerProtocol):
    """Coordonne les différents agents et gère le flux du jeu.
    
    Responsabilités:
    - Initialisation des composants
    - Gestion de l'état du jeu
    - Coordination des agents
    - Traitement des entrées utilisateur
    """
    
    def __init__(
        self,
        agents: Dict[str, AgentProtocols],
        managers: Dict[str, ManagerProtocols],
        game_factory: GameFactory,
        story_graph_config: Optional[AgentConfigBase] = None
    ):
        """Initialize AgentManager.
        
        Args:
            agents: Container with all game agents
            managers: Container with all game managers
            game_factory: GameFactory instance
            story_graph_config: Optional configuration for story graph
            
        Raises:
            GameError: If initialization fails
        """
        logger.info("Initializing AgentManager")
        try:
            # Store containers and config
            self.managers = managers
            self.agents = agents
            self.game_factory = game_factory
            self._story_graph_config = story_graph_config
            
            # Story graph and workflow will be initialized in initialize_game()
            self.story_graph = None
            self._compiled_workflow = None

            logger.info("AgentManager initialization completed")
            
        except Exception as e:
            logger.error("Error initializing AgentManager: {}", str(e))
            raise GameError(
                f"Failed to initialize AgentManager: {str(e)}",
                original_exception=e
            ) from e

    async def get_state(self) -> Optional[GameState]:
        """Get current game state."""
        try:
            logger.debug("Fetching current game state")
            state = await self.managers['state_manager'].get_current_state()
            logger.debug("Current state: {}", state)
            return state
        except Exception as e:
            logger.error("Error getting game state: {}", str(e))
            return None

    # -------------------------------------------------------------------------
    # 1) INITIALISATION DU JEU
    # -------------------------------------------------------------------------
    async def initialize_game(self) -> GameState:
        """
        Initialise un nouveau jeu : crée un état initial, puis lance le workflow
        une première fois pour la “section 1” ou autre.
        """
        try:
            logger.info("Initializing new game")

            # 1. Créer un état initial
            initial_state = await self.managers['state_manager'].create_initial_state()
            # Exemple : session_id, game_id, section_number=1, etc.

            # 2. Convertir en dict complet
            state_dict = initial_state.model_dump(exclude_unset=False)

            # 3. Vérifier session_id / game_id
            if not state_dict.get("session_id"):
                state_dict["session_id"] = initial_state.session_id
            if not state_dict.get("game_id"):
                state_dict["game_id"] = initial_state.game_id

            # 4. Récupérer ou compiler le workflow
            workflow = await self.get_story_workflow()

            # 5. Préparer un thread_config basé sur le session_id
            thread_config = {"configurable": {"thread_id": str(initial_state.session_id)}}

            # 6. Appeler le workflow en “one-shot”
            result = await workflow.ainvoke(state_dict, thread_config)

            # 7. Analyser le résultat
            if isinstance(result, dict):
                # Préserver les IDs si besoin
                if not result.get("session_id"):
                    result["session_id"] = initial_state.session_id
                if not result.get("game_id"):
                    result["game_id"] = initial_state.game_id

                # Construire un nouvel état
                new_state = GameState(**result)
                # Sauvegarder le nouvel état
                await self.managers['state_manager'].save_state(new_state)
                logger.info("Game initialization completed successfully")
                return new_state

            logger.error("Invalid workflow result type: {}", type(result))
            raise GameError("Invalid workflow result")

        except Exception as e:
            logger.error("Error initializing game. Input data: {}, Error: {}", state_dict, str(e))
            raise GameError(
                f"Failed to process game state: {str(e)}",
                original_exception=e
            ) from e

    # -------------------------------------------------------------------------
    # 2) TRAITEMENT DE L’ETAT DU JEU + GESTION DE L’INTERRUPTION
    # -------------------------------------------------------------------------
    async def process_game_state(
        self,
        state: Optional[GameState] = None,
        user_input: Optional[str] = None
    ) -> GameState:
        """
        Gère la suite du jeu : on relance le workflow avec l’état courant (et l’input éventuel).
        Peut lever GraphInterrupt si on attend encore l’utilisateur.
        """
        try:
            logger.info("Starting game state processing")

            if not self.story_graph:
                logger.error("Story graph not initialized")
                raise GameError("Story graph not initialized")

            # 1. Charger l’état courant si non fourni
            if not state:
                state = await self.get_state()
                if not state:
                    raise GameError("No valid state available")

            # 2. Récupérer le workflow
            workflow = await self.get_story_workflow()

            # 3. Mettre à jour l’état avec l’éventuel input
            input_data = state.with_updates(player_input=user_input)

            # 4. Convertir en dict (pour ainvoke)
            state_dict = input_data.model_dump(exclude_unset=False)

            # 5. Double vérification IDs
            if not state_dict.get("session_id"):
                state_dict["session_id"] = state.session_id
            if not state_dict.get("game_id"):
                state_dict["game_id"] = state.game_id

            thread_config = {"configurable": {"thread_id": str(state.session_id)}}

            # 6. Lancer le workflow en one-shot
            try:
                result = await workflow.ainvoke(state_dict, thread_config)
            except GraphInterrupt as gi:
                logger.info("Workflow interrupted: {}", gi)
                # Cas où on n’a pas encore la réponse utilisateur
                if not user_input:
                    # Mettre à jour l’état pour indiquer qu’on attend un input
                    awaiting = state.with_updates(awaiting_input=True)
                    await self.managers['state_manager'].save_state(awaiting)
                    logger.info("Saved state waiting for user input -> raising GraphInterrupt")
                    # On propage l’exception, l’appelant saura qu’il doit reprendre plus tard
                    raise gi

                # Sinon, si l’utilisateur vient d’envoyer son input, on “reprend”
                logger.info("Resuming workflow with user_input={}", user_input)
                result = await workflow.ainvoke(Command(resume=user_input), thread_config)

            # 7. Analyser le résultat final
            if isinstance(result, dict):
                # Si on a “next_section”, on peut créer un nouvel état ou continuer
                if ("decision" in result
                    and result["decision"]
                    and "next_section" in result["decision"]
                    and result["decision"]["next_section"] is not None):
                    next_section = result["decision"]["next_section"]
                    logger.info("Moving to next section: current={} -> next={}",
                                state.section_number, next_section)
                    # Créer un nouvel état si besoin
                    new_state = GameState(
                        session_id=state.session_id,
                        game_id=state.game_id,
                        section_number=next_section,
                        player_input=None
                    )
                    await self.managers['state_manager'].save_state(new_state)
                    logger.info("Created new state for next section")
                    return new_state

                # Sinon, juste mettre à jour l’état actuel
                new_state = state.with_updates(**result)
                await self.managers['state_manager'].save_state(new_state)
                logger.info("Game state processed successfully")
                return new_state

            logger.error("No valid result from workflow")
            raise GameError("No valid result")

        except GraphInterrupt as gi:
            logger.info("Workflow interrupted again: {}", gi)
            # On propage pour que l’appelant sache qu’on est en attente
            raise gi

        except Exception as e:
            logger.error("Error processing game state: {}", str(e))
            raise GameError(f"Failed to process game state: {str(e)}") from e

    async def get_story_workflow(self) -> Any:
        """Get the compiled story workflow.
        
        This method should be called each time we want to start a new workflow instance.
        The workflow will be compiled with the current configuration and managers.
        
        Returns:
            Any: Compiled workflow ready for execution
            
        Raises:
            GameError: If workflow creation fails
        """
        try:
            logger.info("Getting story workflow")
            
            # Ensure story graph exists
            if not self.story_graph:
                logger.debug("Story graph not configured, configuring now")
                self.story_graph = self.game_factory.create_story_graph(
                    config=self._story_graph_config,
                    managers=self.managers,
                    agents=self.agents
                )
            
            # Get or create compiled workflow
            if not self._compiled_workflow:
                logger.debug("Compiling workflow")
                self._compiled_workflow = await self.story_graph.get_compiled_workflow()
            
            return self._compiled_workflow
            
        except Exception as e:
            logger.error("Error getting story workflow: {}", str(e))
            raise GameError(f"Failed to get story workflow: {str(e)}")

    async def get_feedback(self) -> str:
        """Get feedback about the current game state."""
        try:
            logger.info("Getting user feedback")
            current_state = await self.get_state()
            logger.debug("Current state for feedback: {}", current_state)
            
            feedback = await self.managers['trace_manager'].get_state_feedback(current_state)
            logger.debug("Feedback received: {}...", feedback[:100])
            
            return feedback
        except Exception as e:
            logger.error("Error getting user feedback: {}", str(e))
            raise

    async def should_continue(self, state: GameState) -> bool:
        """Check if the game should continue.
        
        This method only checks for error conditions and end game.
        The user input flow is handled by the StoryGraph workflow.
        
        Args:
            state: Current game state
            
        Returns:
            bool: True if game should continue, False if game should stop
        """
        try:
            logger.debug("Checking game continuation for state: {}", state)
            
            # Stop if error
            if state.error:
                logger.info("Game stopped due to error: {}", state.error)
                return False
                
            # Stop if end game
            if getattr(state, 'end_game', False):
                logger.info("Game ended normally")
                return False
                
            logger.debug("Game should continue")
            return True
            
        except Exception as e:
            logger.error("Error checking game continuation: {}", str(e))
            return False

    async def stop_game(self) -> None:
        """Stop the game and save final state."""
        logger.info("Stopping game...")
        try:
            # Vérifie si le game_id est défini avant de sauvegarder
            game_id = await self.managers['state_manager'].get_game_id()
            if not game_id:
                logger.debug("No game ID set, nothing to save")
                return
                
            # Save final state
            current_state = await self.get_state()
            if current_state:
                await self.managers['state_manager'].save_state(current_state)
                logger.info("Final game state saved successfully")
                
            logger.info("Game stopped successfully")
        except Exception as e:
            logger.error("Error stopping game: {}", str(e))
            raise

# Register protocols after class definition
AgentManagerProtocol.register(AgentManager)
StateManagerProtocol.register(StateManagerProtocol)
CacheManagerProtocol.register(CacheManagerProtocol)
CharacterManagerProtocol.register(CharacterManagerProtocol)
TraceManagerProtocol.register(TraceManagerProtocol)
DecisionManagerProtocol.register(DecisionManagerProtocol)
RulesManagerProtocol.register(RulesManagerProtocol)
NarratorManagerProtocol.register(NarratorManagerProtocol)
WorkflowManagerProtocol.register(WorkflowManagerProtocol)

# Register agent protocols
StoryGraphProtocol.register(StoryGraphProtocol)
NarratorAgentProtocol.register(NarratorAgentProtocol)
RulesAgentProtocol.register(RulesAgentProtocol)
DecisionAgentProtocol.register(DecisionAgentProtocol)
TraceAgentProtocol.register(TraceAgentProtocol)
BaseAgentProtocol.register(BaseAgentProtocol)
