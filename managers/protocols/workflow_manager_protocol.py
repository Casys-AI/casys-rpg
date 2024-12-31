"""
Workflow Manager Protocol
Defines the interface for workflow management operations.
"""
from typing import Dict, Any, List, Optional, Protocol, runtime_checkable, AsyncGenerator, Union
from models.game_state import GameState
from models.errors_model import GameError, WorkflowError

@runtime_checkable
class WorkflowManagerProtocol(Protocol):
    """Protocol for workflow management operations."""
        
    async def start_workflow(self, input_data: Optional[Union[Dict[str, Any], GameState]] = None) -> GameState:
        """Start a new workflow instance.
        
        This method:
        1. Validates the input format
        2. Delegates state initialization to StateManager
        3. Sets up the workflow context
        
        Args:
            input_data: Optional initial data for the workflow
                       Can be either a dict or GameState instance
            
        Returns:
            GameState: Initial workflow state
            
        Raises:
            WorkflowError: If workflow initialization fails
        """
        ...
        
    async def end_workflow(self, output_data: GameState) -> GameState:
        """End workflow node.
        
        Finalizes a workflow instance and returns the final output.
        
        Args:
            output_data: Final workflow state
            
        Returns:
            GameState: Final workflow state
            
        Raises:
            WorkflowError: If workflow finalization fails
        """
        ...
        
    async def handle_error(self, error: Exception) -> GameState:
        """Handle workflow errors.
        
        Creates an appropriate error state and handles cleanup.
        
        Args:
            error: The error that occurred
            
        Returns:
            GameState: Error state
        """
        ...
