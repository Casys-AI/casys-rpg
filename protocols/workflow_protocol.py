"""
Protocol for workflow management components.
"""
from typing import Protocol, List, Dict, Any, Optional
from models.game_state import GameState
from models.game_state_output import GameStateOutput


class WorkflowProtocol(Protocol):
    """Protocol for workflow management."""
    
    async def start_workflow(self, state: GameState) -> GameState:
        """Start a new workflow.
        
        Args:
            state: Initial game state
            
        Returns:
            GameState: Updated game state
        """
        ...
        
    async def end_workflow(self, state: GameState) -> GameState:
        """End current workflow.
        
        Args:
            state: Current game state
            
        Returns:
            GameState: Final game state
        """
        ...
        
    async def get_available_transitions(self, state: GameState) -> List[str]:
        """Get available transitions from current state.
        
        Args:
            state: Current game state
            
        Returns:
            List[str]: List of available transitions
        """
        ...
        
    async def execute_game_workflow(
        self,
        story_graph: Any,
        state: GameState,
        input_text: Optional[str] = None
    ) -> GameState:
        """Execute game workflow.
        
        Args:
            story_graph: StoryGraph instance
            state: Current game state
            input_text: Optional user input
            
        Returns:
            GameState: Updated game state
        """
        ...
