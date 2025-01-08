"""
Agent Manager Protocol
Defines the interface for agent management operations.
"""
from typing import Dict, Optional, Any, AsyncGenerator, Protocol, runtime_checkable, TYPE_CHECKING
from models.game_state import GameState
from config.agents.agent_config_base import AgentConfigBase

if TYPE_CHECKING:
    from models.types.agent_types import GameAgents
    from models.types.manager_types import GameManagers
    from agents.factories.game_factory import GameFactory

@runtime_checkable
class AgentManagerProtocol(Protocol):
    """Protocol for agent management operations.
    
    Responsabilités:
    - Initialisation des composants
    - Gestion de l'état du jeu
    - Coordination des agents
    - Traitement des entrées utilisateur
    """
    
    def __init__(
        self,
        agents: 'GameAgents',
        managers: 'GameManagers',
        game_factory: 'GameFactory',
        story_graph_config: Optional['AgentConfigBase'] = None
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
        
        This will:
        1. Initialize the state manager with a new game ID
        2. Create and compile the story workflow
        3. Process the initial game state
        
        Returns:
            GameState: The initial state of the game
            
        Raises:
            GameError: If initialization fails
        """
        ...

    async def get_story_workflow(self) -> Any:
        """Get the compiled story workflow.
        
        This method should be called each time we want to start a new workflow instance.
        The workflow will be compiled with the current configuration and managers.
        
        Returns:
            Any: Compiled workflow ready for execution
            
        Raises:
            GameError: If workflow creation fails
        """
        ...

    async def process_game_state(
        self,  
        user_input: Optional[str] = None
    ) -> GameState:
        """Process game state through the workflow.
        
        The state will be processed through the story workflow:
        1. Rules processing (parallel)
        2. Narrative processing (parallel)
        3. Decision processing
        4. End processing
        
        Args:
            state: Optional game state to use. If None, current state will be used
            user_input: Optional user input to process
            
        Returns:
            GameState: Updated game state
            
        Raises:
            GameError: If processing fails
        """
        ...

    async def get_state(self) -> Optional[GameState]:
        """Get current game state.
        
        Returns:
            Optional[GameState]: Current game state or None if no game is active
        """
        ...

    async def should_continue(self, state: GameState) -> bool:
        """Check if the game should continue.
        
        This method only checks for error conditions and end game.
        The user input flow is handled by the StoryGraph workflow.
        
        Args:
            state: Current game state
            
        Returns:
            bool: True if game should continue, False if game should stop
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

    async def process_section_with_updates(self, section_number: int) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a section with streaming state updates.
        
        Args:
            section_number: Section number to process
            
        Yields:
            Dict: State updates during processing
        """
        ...

    async def stop_game(self) -> None:
        """Stop the game and save final state.
        
        This will:
        1. Save the final state if a game is active
        2. Clean up resources
        
        Raises:
            GameError: If stopping the game fails
        """
        ...