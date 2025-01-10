"""
Agent Manager implementation.
"""

from typing import (
    Any, Optional, Dict, List, Union, Type, TypeVar, Generic)
from loguru import logger
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
from config.agents.agent_config_base import AgentConfigBase

from models.game_state import GameState
from models.errors_model import GameError
from models.decision_model import DecisionModel

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
    async def initialize_game(
        self,
        session_id: Optional[str] = None,
        game_id: Optional[str] = None,
        section_number: Optional[int] = None
    ) -> GameState:
        """Initialize a new game state and run initial workflow.
        
        Args:
            session_id: Optional session ID (will be generated if not provided)
            game_id: Optional game ID (will be generated if not provided)
            section_number: Optional starting section number (default from GameState)
            
        Returns:
            GameState: Initialized game state
        """
        try:
            # 1. Créer l'état initial
            initial_data = {}
            if session_id:
                initial_data['session_id'] = session_id
            if game_id:
                initial_data['game_id'] = game_id
            if section_number:
                initial_data['section_number'] = section_number
                
            state = await self.managers['state_manager'].create_initial_state(initial_data)
            
            # 2. Lancer le workflow initial
            return await self._handle_game_workflow(state)
            
        except Exception as e:
            logger.error("Failed to initialize game: {}", str(e))
            raise GameError(f"Failed to initialize game: {str(e)}") from e

    # -------------------------------------------------------------------------
    # 2) TRAITEMENT DE L’ETAT DU JEU + GESTION DE L’INTERRUPTION
    # -------------------------------------------------------------------------
    async def process_game_state(
        self,
        user_input: Optional[str] = None
    ) -> Optional[GameState]:
        """Process game state and handle workflow.
        
        Args:
            user_input: User input to process (optional)
            
        Raises:
            GameError: If state processing fails
            GraphInterrupt: If waiting for user input
        """
        try:
            # Récupérer l'état actuel
            state = await self.get_state()
            if not state:
                raise GameError("No state available")
                
            # Lancer le workflow avec l'état courant
            return await self._handle_game_workflow(state, user_input)
                
        except GraphInterrupt as gi:
            logger.info("Workflow interrupted: {}", str(gi))
            raise
            
        except Exception as e:
            logger.error("Error processing game state: {}", str(e))
            raise GameError(f"Failed to process game state: {str(e)}") from e


    async def _handle_game_workflow(
            self, 
            state: GameState, 
            user_input: Optional[str] = None
        ) -> GameState:
        """Handle game workflow including state updates and transitions."""
        workflow = await self.get_story_workflow()
        thread_config = {"configurable": {"thread_id": str(state.game_id)}}

        try:
            # Préparer l'état avec `player_input` si fourni
            state_dict = state.model_dump(exclude_unset=False, exclude_none=True)
            logger.debug("[WORKFLOW] State before modification: {}", state_dict)
            
            if user_input:
                logger.debug("[WORKFLOW] Processing user_input: {}", user_input)
                # Vérifier si decision n'existe pas OU est None
                if 'decision' not in state_dict or state_dict['decision'] is None:
                    logger.debug("[WORKFLOW] Creating new decision dict")
                    # Créer un DecisionModel directement sans le convertir en dict
                    state_dict['decision'] = DecisionModel(
                        section_number=state.section_number,
                        player_input=user_input
                    )
                else:
                    logger.debug("[WORKFLOW] Existing decision dict: {}", state_dict['decision'])
                    # Créer un nouveau DecisionModel avec les données existantes + le nouveau player_input
                    existing_decision = state_dict['decision']
                    state_dict['decision'] = DecisionModel(
                        section_number=existing_decision.section_number,
                        player_input=user_input
                    )
                    
                logger.debug("[WORKFLOW] Updated decision dict: {}", state_dict['decision'])

            logger.debug("[WORKFLOW] Initial state_dict: player_input={}, thread_id={}", 
                        state_dict['decision'].player_input if state_dict.get('decision') else None,
                        thread_config["configurable"]["thread_id"])

            # Lancer le workflow avec la commande appropriée
            if user_input:
                logger.info("Resuming workflow with user_input={}", user_input)
                command_data = {"player_input": user_input}
                logger.debug("[WORKFLOW] Command data: {} (type={})", command_data, type(command_data))
                logger.debug("[WORKFLOW] Sending Command(resume={}) with thread_id={}", 
                            command_data, thread_config["configurable"]["thread_id"])
                command = Command(resume=command_data)
                await workflow.ainvoke(command, thread_config)
            else:   
                logger.debug("[WORKFLOW] Starting new workflow with thread_id={}", 
                            thread_config["configurable"]["thread_id"])
                await workflow.ainvoke(state_dict, thread_config)

            # Récupérer l'état mis à jour après l'invocation sans 'await'
            state_snapshot = workflow.get_state(thread_config)
            logger.debug("StateSnapshot retrieved: player_input={}", 
                        state_snapshot.values['decision'].player_input if state_snapshot.values.get('decision') else None)

            # Créer un GameState à partir des valeurs du snapshot
            updated_state = GameState(**state_snapshot.values)

            # Sauvegarder l'état mis à jour
            await self.managers['state_manager'].save_state(updated_state)
            return updated_state
            
        except GraphInterrupt as gi:
            if not user_input:
                # Sauvegarder l'état en attente
                awaiting = state.with_updates(awaiting_input=True)
                await self.managers['state_manager'].save_state(awaiting)
                logger.info("Saved state waiting for user input -> raising GraphInterrupt")
                raise gi

            # Si un input était déjà fourni mais qu'une interruption survient
            logger.warning("Got GraphInterrupt with user_input")
            raise GameError("Unexpected workflow interruption")

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
