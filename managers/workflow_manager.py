"""
Workflow Manager
"""
from typing import Dict, Any, Optional, List, AsyncGenerator, TYPE_CHECKING
from loguru import logger
from pydantic import BaseModel
import uuid
from datetime import datetime

from managers.protocols.workflow_manager_protocol import WorkflowManagerProtocol
from managers.protocols.state_manager_protocol import StateManagerProtocol
from managers.protocols.rules_manager_protocol import RulesManagerProtocol
from models.game_state import GameState
from models.errors_model import GameError, WorkflowError, RulesError

if TYPE_CHECKING:
    from agents.protocols.story_graph_protocol import StoryGraphProtocol

class WorkflowManager(WorkflowManagerProtocol):
    """Workflow Manager implementation."""

    def __init__(
        self,
        state_manager: StateManagerProtocol,

    ):
        """Initialize WorkflowManager.

        Args:
            state_manager: Manager for game state
            rules_manager: Manager for game rules
        """
        logger.info("Initializing WorkflowManager")
        self.state_manager = state_manager
        logger.debug("WorkflowManager initialized with state_manager: {}", 
                    state_manager.__class__.__name__
                    )

    async def handle_error(self, error: Exception) -> GameState:
        """Handle workflow error.

        Args:
            error: Error to handle

        Returns:
            GameState: Error state
        """
        try:
            logger.error("Handling workflow error: {}", str(error))
            return await self.state_manager.create_error_state(str(error))
            
        except Exception as e:
            logger.error("Error handling workflow error: {}", str(e))
            return await self.state_manager.create_error_state(str(e))

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
        try:
            current_section = input_data.get("section_number")
            next_section = input_data.get("next_section")
            
            if next_section is not None:
                logger.info("Workflow transition: section {} -> {}", current_section, next_section)
                input_data["section_number"] = input_data.pop("next_section")
                logger.debug("Section transition complete: now at section {}", input_data["section_number"])
            
            if "section_number" not in input_data:
                logger.warning("No section specified in workflow, starting at section 1")
                input_data["section_number"] = 1
            
            return input_data
            
        except Exception as e:
            error_msg = f"Failed to handle section transition: {str(e)}"
            logger.error(error_msg)
            raise WorkflowError(error_msg) from e

    async def start_workflow(self, input_data: Any) -> GameState:
        """Start the workflow node.
        
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
        try:
            logger.info("Starting workflow")
            
            # 1. Initialiser et valider via StateManager
            if not input_data:
                logger.error("No input data provided")
                raise WorkflowError("No input data provided")
                
            # Laisser StateManager gérer la validation et création
            state = await self.state_manager.create_initial_state(input_data)
            
            # 2. Gérer la transition de section si nécessaire
            state_dict = state.model_dump(exclude_unset=False, exclude_none=False)
            state_dict = await self._handle_section_transition(state_dict)
            
            # 3. Ajouter les métadonnées du workflow
            state_dict["metadata"] = {"node": "start"}
            
            # 4. Sauvegarder l'état final
            final_state = await self.state_manager.validate_state(state_dict)
            saved_state = await self.state_manager.save_state(final_state)
            
            logger.info("Workflow started successfully: session={}, section={}", 
                       saved_state.session_id, 
                       saved_state.game_id,
                       saved_state.section_number)
            
            return saved_state
            
        except Exception as e:
            error_msg = f"Failed to start workflow: {str(e)}"
            logger.error(error_msg)
            raise WorkflowError(error_msg) from e

    async def end_workflow(self, output_data: GameState) -> GameState:
        """End workflow node.

        Finalizes a workflow instance and returns the final output.

        Args:
            output_data: Final workflow output data

        Returns:
            GameState: Final workflow output
        """
        try:
            logger.info("Ending workflow with output: session={}, game={}, section={}", 
                       output_data.session_id,
                       output_data.game_id,
                       output_data.section_number)

            # Save final state
            logger.debug("Saving final state")
            saved_state = await self.state_manager.save_state(output_data)

            logger.info("Workflow ended successfully")
            return saved_state

        except Exception as e:
            logger.error("Error in end node: {}", str(e), exc_info=True)
            # Créer un état d'erreur en utilisant le session_id de l'état courant si possible
            session_id = output_data.session_id if output_data else await self.state_manager.generate_session_id()
            return GameState(
                session_id=session_id,
                section_number=output_data.section_number if output_data else 1,
                error=str(e)
            )