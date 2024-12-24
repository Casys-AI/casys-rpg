"""
Story Graph Protocol Module
Defines the interface for the Story Graph
"""

from typing import Dict, Any, Optional, Protocol
from models.game_state import GameState, GameStateInput, GameStateOutput

class StoryGraphProtocol(Protocol):
    """Protocol for story graph."""
    
    async def _setup_workflow(self) -> None:
        """Configure LangGraph workflow with parallel processing for rules and narrative."""
        ...
        
    async def _process_rules(self, input_data: GameStateInput) -> GameStateOutput:
        """Process game rules for the current state."""
        ...
        
    async def _process_narrative(self, input_data: GameStateInput) -> GameStateOutput:
        """Process narrative for the current state."""
        ...
        
    def _route_after_parallel(self, state: GameStateOutput) -> str:
        """Route to decision after both processes complete."""
        ...
        
    async def _process_decision(self, input_data: GameStateInput) -> GameStateOutput:
        """Process decision for the current state."""
        ...
        
    async def _process_trace(self, input_data: GameStateInput) -> GameStateOutput:
        """Process trace for the current state."""
        ...
        
    async def get_compiled_workflow(self) -> Any:
        """Get the compiled workflow graph.
        
        Returns:
            Any: Compiled workflow graph ready for execution
        """
        ...
