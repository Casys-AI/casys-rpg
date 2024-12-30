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

from langgraph.types import Command
from langgraph.errors import GraphInterrupt

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
            raise GameError(
                f"Failed to process game state: {str(e)}",
                original_exception=e
            ) from e

    async def process_game_state(self, state: Optional[GameState] = None, user_input: Optional[str] = None) -> GameState:
        """Process game state through the workflow."""
        try:
            logger.info("Starting game state processing")
            
            # Vérifier si le story graph est initialisé
            if not self.story_graph:
                logger.error("Story graph not initialized")
                raise GameError("Story graph not initialized")
            
            # Charger l'état actuel si aucun n'est fourni
            if not state:
                logger.debug("No state provided, getting current state")
                state = await self.get_state()
                if not state:
                    logger.error("No valid state available")
                    raise GameError("No valid state available")
            
            # Récupérer le workflow
            workflow = await self.get_story_workflow()
            
            # Préparer les données d'entrée avec la mise à jour de l'utilisateur
            input_data = state.with_updates(player_input=user_input)
            state_dict = input_data.model_dump()
            
            # Ajouter la configuration du thread
            thread_config = {"configurable": {"thread_id": str(state.session_id)}}
            
            # Exécuter le workflow
            async for result in workflow.astream(state_dict, thread_config):
                if isinstance(result, dict):
                    # Préserver les IDs
                    result["session_id"] = state.session_id
                    result["game_id"] = state.game_id
                    
                    # Utiliser next_section comme nouveau section_number si présent
                    if "decision" in result and result["decision"] and "next_section" in result["decision"]:
                        result["section_number"] = result["decision"]["next_section"]
                    
                    new_state = GameState(**result)
                    await self.managers.state_manager.save_state(new_state)
                    logger.info("Game state processed successfully")
                    return new_state
            
            logger.error("No valid result from workflow")
            raise GameError("No valid result")
        
        except GraphInterrupt as gi:
            logger.info("Workflow interrupted: {}", gi)
            # Gérer l'interruption si nécessaire
            raise gi

        except Exception as e:
            logger.error("Error processing game state: {}", str(e))
            raise GameError(
                f"Failed to process game state: {str(e)}",
                original_exception=e
            ) from e



    async def get_state(self) -> Optional[GameState]:
        """Get current game state."""
        try:
            logger.debug("Fetching current game state")
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
            
            # Create input data with preserved IDs
            input_data = GameState(
                session_id=initial_state.session_id,
                game_id=initial_state.game_id,
                state=initial_state,
                metadata={"node": "start"}
            )
            
            # Prepare state dict
            state_dict = input_data.model_dump()
            state_dict["session_id"] = initial_state.session_id
            state_dict["game_id"] = initial_state.game_id
            
            # Add thread_config for LangGraph
            thread_config = {"configurable": {"thread_id": str(initial_state.session_id)}}

            try:
                # Execute workflow
                result = await workflow.ainvoke(state_dict, thread_config)
            except GraphInterrupt as gi:
                logger.info("Workflow interrupted: {}", gi)
                # Example of resuming workflow with user input
                user_input = "Proceed to the next chapter"  # Replace with actual user input
                result = await workflow.ainvoke(Command(resume=user_input), thread_config)
            
            # Validate and save result
            if isinstance(result, dict) and "session_id" in result and "game_id" in result:
                result["session_id"] = initial_state.session_id
                result["game_id"] = initial_state.game_id
                state = GameState(**result)
                await self.managers.state_manager.save_state(state)
                logger.info("Game initialization completed successfully")
                return state
                
            logger.error("Invalid workflow result type: {}", type(result))
            raise GameError("Invalid workflow result")
            
        except Exception as e:
            logger.error("Error initializing game. Input data: {}, Error: {}", state_dict, str(e))
            raise GameError(
                f"Failed to process game state: {str(e)}",
                original_exception=e
            ) from e



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
            
            feedback = await self.managers.trace_manager.get_state_feedback(current_state)
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
