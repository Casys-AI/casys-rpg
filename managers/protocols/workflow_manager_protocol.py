"""
Workflow Manager Protocol
Defines the interface for workflow management operations.
"""
from typing import Dict, Any, List, Optional, Protocol, runtime_checkable, AsyncGenerator
from models.game_state import GameState
from models.errors_model import GameError, WorkflowError

@runtime_checkable
class WorkflowManagerProtocol(Protocol):
    """Protocol for workflow management operations."""
        
    async def start_workflow(self, input_data: Any) -> GameState:
        """Start the workflow node.

        Args:
            input_data: Input state data (can be GameState or dict).

        Returns:
            GameState: Initial workflow state.

        Raises:
            WorkflowError: If input validation or state creation fails.
        """
        ...
        
    async def end_workflow(self, output_data: GameState) -> GameState:
        """End workflow node.

        Finalizes a workflow instance and returns the final output.

        Args:
            output_data: Final workflow output data

        Returns:
            GameState: Final workflow output
        """
        ...
        
    async def handle_error(self, error: Exception) -> GameState:
        """Handle workflow error.

        Args:
            error: Error to handle

        Returns:
            GameState: Error state
        """
        ...
