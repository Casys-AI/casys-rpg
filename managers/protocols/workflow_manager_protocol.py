"""
Workflow Manager Protocol
Defines the interface for workflow management operations.
"""
from typing import Dict, Any, List, Optional, Protocol, runtime_checkable, AsyncGenerator
from models.game_state import GameState, GameStateInput, GameStateOutput
from agents.protocols.story_graph_protocol import StoryGraphProtocol

@runtime_checkable
class WorkflowManagerProtocol(Protocol):
    """Protocol for workflow management operations."""
    
    async def validate_transition(self, from_state: GameState, to_state: GameState) -> bool:
        """Validate if transition between states is valid."""
        ...
        
    async def execute_transition(self, from_state: GameState, to_state: GameState) -> GameState:
        """Execute transition between states."""
        ...
        
    async def get_available_transitions(self, state: GameState) -> Dict[str, Any]:
        """Get available transitions from current state."""
        ...
        
    async def stream_workflow(self, initial_state: GameState) -> AsyncGenerator[GameState, None]:
        """Stream workflow execution."""
        ...
        
    async def handle_error(self, error: Exception) -> GameState:
        """Handle workflow error."""
        ...
        
    async def execute_workflow(
        self,
        story_graph: StoryGraphProtocol,
        state: Optional[GameState] = None,
        user_input: Optional[str] = None
    ) -> GameState:
        """Execute game workflow."""
        ...
        
    async def start_workflow(self, input_data: GameStateInput) -> GameStateOutput:
        """Start workflow node."""
        ...
        
    async def end_workflow(self, output_data: GameStateOutput) -> GameStateOutput:
        """End workflow node."""
        ...
        
    async def initialize_workflow(self, initial_state: GameState) -> None:
        """Initialize workflow with initial state."""
        ...
