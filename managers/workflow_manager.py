"""
Workflow Manager
"""
from typing import Dict, Any, Optional, List, AsyncGenerator
from loguru import logger
from pydantic import BaseModel
import uuid
from datetime import datetime

from managers.protocols.workflow_manager_protocol import WorkflowManagerProtocol
from managers.protocols.state_manager_protocol import StateManagerProtocol
from managers.protocols.rules_manager_protocol import RulesManagerProtocol
from agents.protocols.story_graph_protocol import StoryGraphProtocol
from models.game_state import GameState, GameState, GameState
from models.errors_model import GameError, WorkflowError, RulesError


class WorkflowManager(WorkflowManagerProtocol):
    """Workflow Manager implementation."""

    def __init__(
        self,
        state_manager: StateManagerProtocol,
        rules_manager: RulesManagerProtocol
    ):
        """Initialize WorkflowManager.

        Args:
            state_manager: Manager for game state
            rules_manager: Manager for game rules
        """
        logger.info("Initializing WorkflowManager")
        self.state_manager = state_manager
        self.rules_manager = rules_manager
        logger.debug("WorkflowManager initialized with state_manager: {}, rules_manager: {}", 
                    state_manager.__class__.__name__, 
                    rules_manager.__class__.__name__)

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

    async def start_workflow(self, input_data: Any) -> GameState:
        """Start the workflow node.

        Args:
            input_data: Input state data (can be GameState or dict).

        Returns:
            GameState: Initial workflow state.

        Raises:
            WorkflowError: If input validation or state creation fails.
        """
        try:
            logger.info("Starting workflow node")
            logger.debug("Input data received: Type: {}, Value: {}", type(input_data), input_data)

            # Validation des données d'entrée
            if not input_data:
                raise WorkflowError("No input data provided")

            # Conversion en GameState si nécessaire
            if isinstance(input_data, dict):
                logger.debug("Input data is a dictionary, converting to GameState")
                state = GameState(**input_data)
            elif isinstance(input_data, GameState):
                logger.debug("Input data is already a GameState")
                state = input_data
            else:
                raise WorkflowError(f"Invalid input data type: {type(input_data)}. Expected GameState or dict.")

            # Créer ou mettre à jour l'état avec with_updates
            if not getattr(state, "session_id", None) or not getattr(state, "game_id", None):
                logger.debug("Creating initial state with session_id and game_id")
                initial_state = await self.state_manager.create_initial_state()
                state = initial_state.with_updates(**state.model_dump())
            logger.debug("Validated state session_id: {} and game_id: {}", state.session_id, state.game_id)

            # Mise à jour du section_number si next_section est présent dans la décision
            if state.decision and state.decision.next_section is not None:
                logger.debug("Found next_section in decision: {}", state.decision.next_section)
                state = state.with_updates(section_number=state.decision.next_section)

            # Sauvegarder l'état
            state = state.with_updates(metadata={"node": "start"})
            saved_state = await self.state_manager.save_state(state)
            
            logger.info("Successfully created and saved output with session_id: {} and section_number: {}", 
                       saved_state.session_id, saved_state.section_number)
            return saved_state

        except Exception as e:
            logger.error("Error starting workflow. Input data: {}, Error: {}", input_data, str(e))
            raise WorkflowError(str(e)) from e

    async def end_workflow(self, output_data: GameState) -> GameState:
        """End workflow node.

        Finalizes a workflow instance and returns the final output.

        Args:
            output_data: Final workflow output data

        Returns:
            GameState: Final workflow output
        """
        try:
            logger.info("Ending workflow with output: session={}, section={}", 
                       output_data.session_id, 
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