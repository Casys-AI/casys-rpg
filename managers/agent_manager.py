"""
Agent Manager implementation.
"""

from typing import (
    Dict, Any, Optional, List, Tuple, Type,
    AsyncGenerator, AsyncIterator, Protocol
)
import uuid
from datetime import datetime
from loguru import logger

from fastapi import Depends

from managers.state_manager import StateManager
from managers.cache_manager import CacheManager
from managers.character_manager import CharacterManager
from managers.trace_manager import TraceManager
from managers.decision_manager import DecisionManager
from managers.rules_manager import RulesManager
from managers.narrator_manager import NarratorManager
from managers.workflow_manager import WorkflowManager

from agents.story_graph import StoryGraph
from agents.narrator_agent import NarratorAgent
from agents.rules_agent import RulesAgent
from agents.decision_agent import DecisionAgent
from agents.trace_agent import TraceAgent
from agents.base_agent import BaseAgent

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

from config.storage_config import StorageConfig

import asyncio

_agent_manager = None

def get_game_factory() -> GameFactory:
    """Get GameFactory instance."""
    logger.debug("Creating new GameFactory instance")
    return GameFactory()

def get_storage_config() -> StorageConfig:
    """Get StorageConfig instance."""
    logger.debug("Creating new StorageConfig instance")
    return StorageConfig()

def get_agent_manager(
    game_factory: GameFactory = Depends(get_game_factory),
    storage_config: StorageConfig = Depends(get_storage_config)
) -> AgentManagerProtocol:
    """Get or create AgentManager instance."""
    global _agent_manager
    
    if not _agent_manager:
        logger.info("Creating new AgentManager instance")
        managers = game_factory._create_managers()
        agents = game_factory._create_agents(managers)
        _agent_manager = AgentManager(agents, managers, game_factory)
        logger.debug("AgentManager initialized with factory: %s and config: %s", 
                    game_factory.__class__.__name__, 
                    storage_config.__class__.__name__)
    else:
        logger.debug("Returning existing AgentManager instance")
        
    return _agent_manager

class AgentManager:
    """
    Coordonne les différents agents et gère le flux du jeu.
    
    Responsabilités:
    - Initialisation des composants
    - Gestion de l'état du jeu
    - Coordination des agents
    - Traitement des entrées utilisateur
    """
    
    def __init__(
            self,
            agents: GameAgents,
            managers: GameManagers,
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
            raise GameError(f"Failed to initialize AgentManager: {str(e)}")

    async def process_game_state(self, state: Optional[GameState] = None, user_input: Optional[str] = None) -> GameState:
        """Process game state through the workflow.
        
        Args:
            state: Optional game state to use
            user_input: Optional user input
            
        Returns:
            GameState: Updated game state
            
        Raises:
            GameError: If processing fails
        """
        try:
            logger.info("Starting game state processing")
            logger.debug("Input state: {}, User input: {}", state, user_input)
            
            if not self.story_graph:
                logger.error("Story graph not initialized")
                raise GameError("Story graph not initialized")
                
            # Get current state if none provided
            if not state:
                logger.debug("No state provided, getting current state")
                state = await self.get_state()
                
                if not state and self.managers.state_manager:
                    logger.debug("Creating initial state")
                    state = await self.managers.state_manager.create_initial_state()
                    
            if not state:
                logger.error("No valid state available")
                raise GameError("No valid state available")
                
            # Compile workflow
            workflow = await self.get_story_workflow()
            
            # Create input and execute
            input_data = state.with_updates(player_input=user_input)
            async for result in workflow.astream(input_data):
                if isinstance(result, GameState):
                    return result
                    
            logger.error("No valid result from workflow")
            raise GameError("No valid result")
            
        except Exception as e:
            logger.error("Error processing game state: {}", str(e))
            raise GameError(str(e))

    async def get_state(self) -> Optional[GameState]:
        """Get current game state."""
        try:
            logger.debug("Fetching current game state")
            # Vérifie si le game_id est défini avant d'accéder au state
            if not await self.managers.state_manager.get_game_id():
                logger.debug("No game ID set, returning None")
                return None
                
            state = await self.managers.state_manager.get_current_state()
            logger.debug("Current state: {}", state)
            return state
        except Exception as e:
            logger.error("Error getting game state: {}", str(e))
            return None

    async def initialize_game(self) -> GameState:
        """Initialize and setup a new game instance.

        Returns:
            GameState: The initial state of the game

        Raises:
            GameError: If initialization fails
        """
        try:
            logger.info("Initializing game")
            
            # Get workflow (will create story graph if needed)
            workflow = await self.get_story_workflow()
            
            # Create initial state
            initial_state = await self.managers.state_manager.create_initial_state()
            
            # Create input data
            input_data = GameState(
                session_id=initial_state.session_id,
                state=initial_state,
                metadata={"node": "start"}
            )
            
            # Execute workflow
            result = await workflow.ainvoke(input_data.model_dump())
            
            if isinstance(result, dict):
                state = GameState(**result)
                await self.managers.state_manager.save_state(state)
                logger.info("Game initialization completed successfully")
                return state
                
            logger.error("Invalid workflow result type: {}", type(result))
            raise GameError("Invalid workflow result")
            
        except Exception as e:
            logger.error("Error initializing game: {}", str(e))
            raise GameError(f"Failed to initialize game: {str(e)}")

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

    async def stream_game_state(self) -> AsyncGenerator[Dict, None]:
        """Stream game state updates.
        
        Yields:
            Dict: Game state updates
            
        Raises:
            GameError: If streaming fails
        """
        try:
            logger.info("Starting game state streaming")
            
            # Get current state
            current_state = await self.get_state()
            if not current_state:
                logger.error("No current state available")
                raise GameError("No current state available")
                
            # Create input data
            logger.debug("Creating input data")
            input_data = GameState(
                session_id=current_state.session_id,
                state=current_state,
                metadata={"node": "stream"}
            )
            
            # Get workflow
            logger.debug("Getting compiled workflow")
            workflow = await self.get_story_workflow()
            logger.debug("Starting workflow streaming")
            
            # Stream workflow results
            async for result in workflow.astream(input_data.model_dump()):
                if isinstance(result, dict):
                    logger.debug("Processing workflow result")
                    state = GameState(**result)
                    
                    # Check if game should continue
                    if not await self.should_continue(state):
                        logger.info("Game should not continue, stopping streaming")
                        return
                
                    # Save state
                    logger.debug("Saving updated state")
                    await self.managers.state_manager.save_state(state)
                    logger.debug("Yielding state update")
                    yield state.model_dump()
                else:
                    logger.error("Invalid workflow result type: {}", type(result))
                    raise GameError("Invalid workflow result")
            
        except Exception as e:
            logger.error("Error streaming game state: {}", str(e))
            raise GameError(f"Failed to stream game state: {str(e)}")

    async def get_feedback(self) -> str:
        """Get feedback about the current game state."""
        try:
            logger.info("Getting user feedback")
            current_state = await self.get_state()
            logger.debug("Current state for feedback: {}", current_state)
            
            feedback = await self.managers.trace_manager.get_state_feedback(current_state)
            logger.debug("Feedback received: {}...", feedback[:100])
            
            return feedback
        except Exception as e:
            logger.error("Error getting user feedback: {}", str(e))
            raise

    async def should_continue(self, state: GameState) -> bool:
        """Check if the game should continue."""
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
            
            # Stop si on attend une réponse utilisateur
            if state.rules and state.rules.needs_user_response:
                logger.info("Waiting for user input")
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
            game_id = await self.managers.state_manager.get_game_id()
            if not game_id:
                logger.debug("No game ID set, nothing to save")
                return
                
            # Save final state
            current_state = await self.get_state()
            if current_state:
                await self.managers.state_manager.save_state(current_state)
                logger.info("Final game state saved successfully")
                
            logger.info("Game stopped successfully")
        except Exception as e:
            logger.error("Error stopping game: {}", str(e))
            raise

# Register protocols after class definition
AgentManagerProtocol.register(AgentManager)
StateManagerProtocol.register(StateManager)
CacheManagerProtocol.register(CacheManager)
CharacterManagerProtocol.register(CharacterManager)
TraceManagerProtocol.register(TraceManager)
DecisionManagerProtocol.register(DecisionManager)
RulesManagerProtocol.register(RulesManager)
NarratorManagerProtocol.register(NarratorManager)
WorkflowManagerProtocol.register(WorkflowManager)

# Register agent protocols
StoryGraphProtocol.register(StoryGraph)
NarratorAgentProtocol.register(NarratorAgent)
RulesAgentProtocol.register(RulesAgent)
DecisionAgentProtocol.register(DecisionAgent)
TraceAgentProtocol.register(TraceAgent)
BaseAgentProtocol.register(BaseAgent)
