"""
Story Graph Protocol Module
Defines the interface for the Story Graph
"""

from typing import Dict, Any, Optional, Protocol
from models.game_state import GameState

class StoryGraphProtocol(Protocol):
    """Protocol for story graph."""
    
    async def _setup_workflow(self) -> None:
        """Setup workflow graph."""
        ...
        
    async def process_user_input(self, input_text: str) -> GameState:
        """Process user input and update game state.
        
        Args:
            input_text: User input text
            
        Returns:
            GameState: Updated game state
        """
        ...
        
    async def _compile_workflow(self) -> Any:
        """Compile workflow graph.
        
        Returns:
            Any: Compiled workflow
        """
        ...
