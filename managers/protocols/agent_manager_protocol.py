"""
Agent Manager Protocol
Defines the interface for agent management operations.
"""
from typing import Dict, Optional, Any, AsyncGenerator, Protocol, runtime_checkable, TYPE_CHECKING
from models.game_state import GameState
from config.agents.agent_config_base import AgentConfigBase
from agents.factories.game_factory import GameFactory

if TYPE_CHECKING:
    from models.types.agent_types import GameAgents
    from models.types.manager_types import GameManagers

@runtime_checkable
class AgentManagerProtocol(Protocol):
    """Protocol for agent management operations."""
    
    def __init__(
        self,
        agents: 'GameAgents',
        managers: 'GameManagers',
        game_factory: GameFactory,
        story_graph_config: Optional[AgentConfigBase] = None
    ) -> None:
        """Initialize agent manager.
        
        Args:
            agents: Container with all game agents
            managers: Container with all game managers
            game_factory: GameFactory instance
            story_graph_config: Optional configuration for story graph
            
        Raises:
            GameError: If initialization fails
        """
        ...

    async def initialize_game(self) -> GameState:
        """Initialize and setup a new game instance.

        Returns:
            GameState: The initial state of the game

        Raises:
            GameError: If initialization encounters an error
        """
        ...

    async def get_story_workflow(self) -> Any:
        """Get the compiled story workflow.
        
        Returns:
            Any: Compiled workflow ready for execution
            
        Raises:
            GameError: If workflow creation fails
        """
        ...

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
        ...

    async def process_user_input(self, input_text: str) -> GameState:
        """Process user input and update game state.
        
        Args:
            input_text: User input text
            
        Returns:
            GameState: Updated game state
            
        Raises:
            GameError: If input processing fails
        """
        ...

    async def get_state(self) -> Optional[GameState]:
        """Get current game state."""
        ...

    async def should_continue(self, state: GameState) -> bool:
        """Check if the game should continue.
        
        Args:
            state: Current game state
            
        Returns:
            bool: True if game should continue
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
    