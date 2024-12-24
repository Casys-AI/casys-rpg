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

from agents.factories.game_factory import GameFactory, GameAgents, GameManagers
from config.agents.agent_config_base import AgentConfigBase

from models.game_state import GameState, GameStateInput, GameStateOutput
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
        _agent_manager = AgentManager(agents, managers)
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
    
    def _validate_managers(self, managers: GameManagers) -> None:
        """Validate that all required managers are present and properly initialized."""
        required_managers = [
            (managers.state_manager, "StateManager"),
            (managers.cache_manager, "CacheManager"),
            (managers.character_manager, "CharacterManager"),
            (managers.trace_manager, "TraceManager"),
            (managers.decision_manager, "DecisionManager"),
            (managers.rules_manager, "RulesManager"),
            (managers.narrator_manager, "NarratorManager"),
            (managers.workflow_manager, "WorkflowManager")
        ]
        
        for manager, name in required_managers:
            if not manager:
                raise GameError(f"Required manager {name} is not initialized")
                
    def _validate_agents(self, agents: GameAgents) -> None:
        """Validate that all required agents are present and properly initialized."""
        required_agents = [
            (agents.narrator_agent, "NarratorAgent"),
            (agents.rules_agent, "RulesAgent"),
            (agents.decision_agent, "DecisionAgent"),
            (agents.trace_agent, "TraceAgent")
        ]
        
        for agent, name in required_agents:
            if not agent:
                raise GameError(f"Required agent {name} is not initialized")

    def __init__(
            self,
            agents: GameAgents,
            managers: GameManagers,
            story_graph_config: Optional[AgentConfigBase] = None
        ):
        """Initialize AgentManager.
        
        Args:
            agents: Container with all game agents
            managers: Container with all game managers
            story_graph_config: Optional configuration for story graph
            
        Raises:
            GameError: If any required component is missing or not properly initialized
        """
        logger.info("Initializing AgentManager")
        try:
            # Validate components
            self._validate_managers(managers)
            self._validate_agents(agents)
            
            # Store containers and config
            self.managers = managers
            self.agents = agents
            self._story_graph_config = story_graph_config
            self._initialized = False
            
            # Story graph will be initialized in initialize_game()
            self.story_graph = None
            
            logger.info("AgentManager initialization completed")
            
        except Exception as e:
            logger.error("Error initializing AgentManager: {}", str(e))
            raise GameError(f"Failed to initialize AgentManager: {str(e)}")

    async def execute_workflow(self, state: Optional[GameState] = None, user_input: Optional[str] = None) -> GameState:
        """Execute game workflow."""
        try:
            logger.info("Starting workflow execution")
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
                
            # Execute workflow through story graph
            logger.debug("Executing game workflow through story graph")
            state = await self.workflow_manager.execute_workflow(
                state=state,
                user_input=user_input,
                story_graph=self.story_graph
            )
            logger.info("Workflow execution completed successfully")
            return state
            
        except Exception as e:
            logger.error("Error executing workflow: {}", str(e))
            if isinstance(e, GameError):
                error_message = str(e)
            else:
                error_message = f"Unexpected error: {str(e)}"
                
            if self.managers.state_manager:
                logger.debug("Creating error state")
                return await self.managers.state_manager.create_error_state(error_message)
            raise GameError(error_message)

    async def process_user_input(self, input_text: str) -> GameState:
        """Process user input and update game state."""
        try:
            logger.info("Processing user input: {}", input_text)
            result = await self.execute_workflow(user_input=input_text)
            logger.debug("User input processing completed with result: {}", result)
            return result
            
        except Exception as e:
            logger.error("Error processing user input: {}", str(e))
            raise

    async def navigate_to_section(self, section_number: int) -> GameState:
        """Navigate to a specific section."""
        try:
            logger.info("Navigating to section {}", section_number)
            current_state = await self.get_state()
            logger.debug("Current state: {}", current_state)
            if current_state:
                current_state.section_number = section_number
            logger.debug("Updated state: {}", current_state)
            result = await self.execute_workflow(state=current_state)
            logger.debug("Navigation completed with result: {}", result)
            return result
            
        except Exception as e:
            logger.error("Error navigating to section: {}", str(e))
            raise

    async def perform_action(self, action: Dict[str, Any]) -> GameState:
        """Process a user's game action."""
        try:
            logger.info("Performing action: {}", action)
            input_text = str(action.get("response", ""))
            logger.debug("Converting action to input: {}", input_text)
            result = await self.execute_workflow(user_input=input_text)
            logger.debug("Action processing completed with result: {}", result)
            return result
            
        except Exception as e:
            logger.error("Error performing action: {}", str(e))
            raise

    async def submit_response(self, response: str) -> GameState:
        """Process a user's response or decision."""
        try:
            logger.info("Processing user response: {}", response)
            result = await self.execute_workflow(user_input=response)
            logger.debug("Response processing completed with result: {}", result)
            return result
            
        except Exception as e:
            logger.error("Error processing user response: {}", str(e))
            raise

    async def process_section(self, section_number: int) -> GameState:
        """Process a new game section."""
        try:
            logger.info("Processing section {}", section_number)
            current_state = await self.get_state()
            logger.debug("Current state: {}", current_state)
            if current_state:
                current_state.section_number = section_number
            logger.debug("Updated state: {}", current_state)
            result = await self.execute_workflow(state=current_state)
            logger.debug("Section processing completed with result: {}", result)
            return result
            
        except Exception as e:
            logger.error("Error processing section {}: {}", section_number, str(e))
            raise

    async def _initialize_components(self) -> None:
        """Initialize all manager components that have an initialize method."""
        logger.info("Initializing manager components")
        
        # Utilise les champs de la dataclass directement
        for field in self.managers.__dataclass_fields__:
            manager = getattr(self.managers, field)
            if hasattr(manager, 'initialize'):
                logger.debug("Initializing {}", field)
                await manager.initialize()

    async def initialize(self) -> None:
        """Initialize the agent manager and its components."""
        if self._initialized:
            logger.debug("AgentManager already initialized")
            return
        
        try:
            logger.info("Starting AgentManager initialization")
            
            # Initialize all manager components
            await self._initialize_components()
            
            self._initialized = True
            logger.info("AgentManager initialization completed successfully")
            
        except Exception as e:
            logger.error("Error during AgentManager initialization: {}", str(e))
            raise GameError(f"Failed to initialize AgentManager: {str(e)}")

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

    async def initialize_game(
        self,
        session_id: str,
        init_params: Dict[str, Any]
    ) -> GameState:
        """Initialize a new game session.
        
        Args:
            session_id: Unique session identifier
            init_params: Initial game parameters
            
        Returns:
            GameState: Initial game state
        """
        try:
            # Ensure manager is initialized
            if not self._initialized:
                await self.initialize()
            
            # Configure story graph
            self.story_graph = self._configure_story_graph()
            if not self.story_graph:
                raise GameError("Story graph configuration failed")
            await self.story_graph._setup_workflow()

            # Create initial state
            initial_state = GameState(
                session_id=session_id,
                section_number=1,
                last_update=self.managers.state_manager.get_current_timestamp(),
                **init_params
            )
            
            # Initialize and execute workflow
            await self.managers.workflow_manager.initialize_workflow(initial_state)
            updated_state = await self.managers.workflow_manager.execute_workflow(
                state=initial_state,
                user_input=None,
                story_graph=self.story_graph
            )
            
            return updated_state
            
        except Exception as e:
            logger.error("Error during game initialization: {}", str(e))
            raise GameError(f"Failed to initialize game: {str(e)}")

    async def stream_game_state(self) -> AsyncGenerator[Dict, None]:
        """Stream game state updates.
        
        Yields:
            Dict: Game state updates
            
        Raises:
            GameError: If streaming fails
        """
        try:
            logger.info("Starting game state streaming")
            
            # Get initial state
            logger.debug("Getting initial state")
            initial_state = await self.managers.state_manager.get_current_state()
            if not initial_state:
                logger.debug("No current state found, creating initial state")
                initial_state = await self.managers.state_manager.create_initial_state()
                
            # Create input data with timestamp
            logger.debug("Creating input data")
            current_time = self.managers.state_manager.get_current_timestamp()
            logger.debug("Current timestamp: {}", current_time)
            input_data = GameStateInput(
                state=initial_state,
                metadata={"timestamp": current_time}
            )
            
            # Initialize workflow if needed
            if not self.story_graph or self.story_graph._graph is None:
                logger.debug("Story graph not initialized, setting up workflow")
                await self.story_graph._setup_workflow()
            
            # Get workflow
            logger.debug("Compiling workflow")
            workflow = self.story_graph._graph.compile()
            logger.debug("Executing workflow")
            result = await workflow.ainvoke(input_data.model_dump())
            
            if isinstance(result, dict):
                logger.debug("Processing workflow result")
                output = GameStateOutput(**result)
                
                # Update available transitions
                logger.debug("Getting available transitions")
                transitions = await self.managers.workflow_manager.get_available_transitions(output.state)
                output.state.next_steps = transitions
            
                # Save state
                logger.debug("Saving updated state")
                await self.managers.state_manager.save_state(output.state)
                logger.info("State streaming completed successfully")
                yield output.model_dump()
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
                
            # Stop if no valid section
            if not state.section_number:
                logger.error("No valid section number")
                return False
                
            logger.debug("Game should continue")
            return True
            
        except Exception as e:
            logger.error("Error checking game continuation: {}", str(e))
            return False

    async def process_section_with_updates(self, section_number: int) -> AsyncGenerator[GameState, None]:
        """Process a section with streaming state updates."""
        try:
            logger.info("Processing section {} with updates", section_number)
            
            # Initialize story graph if needed
            if not self.story_graph:
                logger.info("Story graph not initialized, initializing now")
                await self.initialize()
                
            # Get initial state
            initial_state = await self.get_state()
            logger.debug("Initial state: {}", initial_state)
            
            if initial_state:
                initial_state.section_number = section_number
                await self.managers.state_manager.save_state(initial_state)
            
            # Stream updates via story graph
            async for state in self.stream_game_state():
                logger.debug("State update: {}", state)
                if isinstance(state, dict):
                    state = GameState(**state)
                yield state
                
        except Exception as e:
            logger.error("Error processing section with updates: {}", str(e))
            raise

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

    def get_agent(self, agent_type: str) -> BaseAgentProtocol:
        """Get agent instance by type.
        
        Args:
            agent_type: Type of agent to get
            
        Returns:
            BaseAgentProtocol: Agent instance
            
        Raises:
            ValueError: If agent type is not found
        """
        try:
            if not self.agents:
                raise ValueError("Agents not initialized")
                
            if hasattr(self.agents, agent_type):
                return getattr(self.agents, agent_type)
            
            raise ValueError(f"Unknown agent type: {agent_type}")
            
        except Exception as e:
            logger.error("Error getting agent {}: {}", agent_type, str(e))
            raise

    def _configure_story_graph(self) -> StoryGraphProtocol:
        """Configure the story graph with all dependencies.
        
        Returns:
            StoryGraphProtocol: Configured story graph instance
        """
        try:
            logger.debug("Configuring story graph")
            
            # Create story graph with config and managers
            story_graph = StoryGraph(
                config=self._story_graph_config,
                managers=self.managers,
                agents=self.agents
            )
            
            logger.debug("Story graph configured successfully")
            return story_graph
            
        except Exception as e:
            logger.error("Error configuring story graph: {}", str(e))
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

StoryGraphProtocol.register(StoryGraph)
NarratorAgentProtocol.register(NarratorAgent)
RulesAgentProtocol.register(RulesAgent)
DecisionAgentProtocol.register(DecisionAgent)
TraceAgentProtocol.register(TraceAgent)
BaseAgentProtocol.register(BaseAgent)
