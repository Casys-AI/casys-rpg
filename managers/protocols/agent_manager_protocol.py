"""
Agent Manager Protocol
Defines the interface for agent management and coordination.
"""
from typing import Dict, Optional, Any, AsyncGenerator, Protocol, runtime_checkable
from models.game_state import GameState
from agents.protocols.base_agent_protocol import BaseAgentProtocol
from agents.factories.game_factory import GameAgents, GameManagers
from config.agents.agent_config_base import AgentConfigBase

@runtime_checkable
class AgentManagerProtocol(Protocol):
    """Protocol for agent management operations."""
    
    def __init__(
        self,
        agents: GameAgents,
        managers: GameManagers,
        story_graph_config: Optional[AgentConfigBase] = None
    ) -> None:
        """Initialize agent manager.
        
        Args:
            agents: Container with all game agents
            managers: Container with all game managers
            story_graph_config: Optional configuration for story graph
            
        Raises:
            GameError: If any required component is missing or not properly initialized
        """
        ...
        
    async def execute_workflow(
        self,
        state: Optional[GameState] = None,
        user_input: Optional[str] = None
    ) -> GameState:
        """Execute game workflow.
        
        Args:
            state: Optional current game state
            user_input: Optional user input
            
        Returns:
            GameState: Updated game state
        """
        ...
        
    async def process_user_input(self, input_text: str) -> GameState:
        """Process user input and update game state.
        
        Args:
            input_text: User input text
            
        Returns:
            GameState: Updated game state
        """
        ...
        
    async def navigate_to_section(self, section_number: int) -> GameState:
        """Navigate to a specific section.
        
        Args:
            section_number: Target section number
            
        Returns:
            GameState: Updated game state
        """
        ...
        
    async def perform_action(self, action: Dict[str, Any]) -> GameState:
        """Process a user's game action.
        
        Args:
            action: Action details
            
        Returns:
            GameState: Updated game state
        """
        ...
        
    async def submit_response(self, response: str) -> GameState:
        """Process a user's response or decision.
        
        Args:
            response: User response
            
        Returns:
            GameState: Updated game state
        """
        ...
        
    async def process_section(self, section_number: int) -> GameState:
        """Process a new game section.
        
        Args:
            section_number: Section number to process
            
        Returns:
            GameState: Updated game state
        """
        ...
        
    async def initialize(self) -> None:
        """Initialize the agent manager and its components."""
        ...
        
    async def get_state(self) -> Optional[GameState]:
        """Get current game state.
        
        Returns:
            Optional[GameState]: Current game state or None
        """
        ...
        
    async def initialize_game(self) -> GameState:
        """Initialize and setup a new game instance.
        
        This method performs the following steps:
        1. Ensures the manager is initialized
        2. Configures and sets up the story graph
        3. Initializes the game workflow
        
        Returns:
            GameState: The initial state of the game
            
        Raises:
            GameError: If story graph configuration fails or initialization encounters an error
        """
        ...
        
    async def stream_game_state(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream game state updates.
        
        Yields:
            Dict: Game state updates
            
        Raises:
            GameError: If streaming fails
        """
        ...
        
    async def get_feedback(self) -> str:
        """Get feedback about the current game state.
        
        Returns:
            str: Formatted feedback
        """
        ...
        
    def should_continue(self, state: GameState) -> bool:
        """Check if the game should continue.
        
        Args:
            state: Current game state
            
        Returns:
            bool: True if game should continue
        """
        ...
    
    async def process_section_with_updates(self, section_number: int) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a section with streaming state updates.
        
        Args:
            section_number: Section number to process
            
        Yields:
            Dict: State updates during processing
        """
        ...
    
    async def stop_game(self) -> None:
        """Stop the game and save final state."""
        ...
    
    def get_agent(self, agent_type: str) -> BaseAgentProtocol:
        """Get agent instance by type.
        
        Args:
            agent_type: Type of agent to get
            
        Returns:
            BaseAgentProtocol: Agent instance
            
        Raises:
            ValueError: If agent type is not found
        """
        ...
