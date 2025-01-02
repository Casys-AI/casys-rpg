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
        
    async def start_workflow(self, input_data: Any) -> GameState:
        """Start a new workflow instance.
        
        Handles the workflow-specific aspects of starting a game session:
        1. Validates and processes input data via StateManager
        2. Manages section transitions
        3. Adds workflow metadata
        
        Args:
            input_data: Input data for the workflow
            
        Returns:
            GameState: Initialized and processed game state
            
        Raises:
            WorkflowError: If workflow start fails
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
            GameState: Error state containing workflow error information
            
        Raises:
            WorkflowError: If error handling itself fails
        """
        ...

    async def _handle_section_transition(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle section number transition in the workflow.
        
        Manages the transition from next_section to section_number in the game flow:
        1. If next_section exists, it becomes the new section_number
        2. Ensures a default section number if none is specified
        3. Logs the transition for workflow tracing
        
        Args:
            input_data: Input data containing section information
            
        Returns:
            Dict[str, Any]: Updated input data with correct section number
            
        Raises:
            WorkflowError: If section transition fails
        """
        ...
