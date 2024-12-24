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
        
    async def execute_transition(self, from_state: GameState, to_state: GameState) -> GameState:
        """Execute transition between states.
        
        The transition is assumed to be already validated by the DecisionAgent.
        This method only handles the state update and persistence.
        
        Args:
            from_state: Source state
            to_state: Target state (already validated by DecisionAgent)
            
        Returns:
            GameState: Updated state after transition
        """
        ...
        
    async def stream_workflow(self, initial_state: GameState) -> AsyncGenerator[GameState, None]:
        """Stream workflow execution.
        
        Provides a stream of game states as the workflow progresses.
        
        Args:
            initial_state: Initial game state
            
        Returns:
            AsyncGenerator[GameState, None]: Stream of game states
        """
        ...
        
    async def handle_error(self, error: Exception) -> GameState:
        """Handle workflow error.
        
        Creates an error state when workflow execution fails.
        
        Args:
            error: Exception that occurred
            
        Returns:
            GameState: Error state
        """
        ...
        
    async def execute_workflow(
        self,
        story_graph: StoryGraphProtocol,
        initial_state: Optional[GameState] = None
    ) -> GameState:
        """Execute game workflow.
        
        Executes the main game workflow using the story graph.
        
        Args:
            story_graph: Story graph instance for workflow control
            initial_state: Optional initial state
            
        Returns:
            GameState: Final state after workflow execution
        """
        ...
        
    async def start_workflow(self, input_data: GameStateInput) -> GameStateOutput:
        """Start workflow node.
        
        Initializes a new workflow instance with the given input.
        
        Args:
            input_data: Input data for workflow
            
        Returns:
            GameStateOutput: Initial workflow output
        """
        ...
        
    async def end_workflow(self, output_data: GameStateOutput) -> GameStateOutput:
        """End workflow node.
        
        Finalizes a workflow instance and returns the final output.
        
        Args:
            output_data: Final workflow output data
            
        Returns:
            GameStateOutput: Final workflow output
        """
        ...
