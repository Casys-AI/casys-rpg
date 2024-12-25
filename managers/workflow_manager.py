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

    async def execute_transition(self, from_state: GameState, to_state: GameState) -> GameState:
        """Execute transition between states.

        Args:
            from_state: Source state
            to_state: Target state (déjà validé par le DecisionAgent)

        Returns:
            GameState: Updated state after transition

        Raises:
            WorkflowError: If transition fails
        """
        try:
            logger.info("Executing transition from section {} to {}", 
                       from_state.section_number if from_state else None,
                       to_state.section_number if to_state else None)

            # Update state with transition info
            to_state.last_state = from_state.section_number
            to_state.timestamp = datetime.now()

            # Save new state
            logger.debug("Saving new state")
            final_state = await self.state_manager.save_state(to_state)
            logger.info("Transition completed successfully")
            return final_state

        except Exception as e:
            logger.error("Error executing transition: {}", str(e), exc_info=True)
            raise WorkflowError(f"Failed to execute transition: {str(e)}")

    async def stream_workflow(self, initial_state: GameState) -> AsyncGenerator[GameState, None]:
        """Stream workflow execution.

        Args:
            initial_state: Initial game state

        Yields:
            GameState: Updated game states

        Raises:
            WorkflowError: If streaming fails
        """
        try:
            logger.info("Starting workflow streaming from section {}", initial_state.section_number)
            current_state = initial_state

            while True:
                # 1. Get available transitions
                logger.debug("Getting available transitions for section {}", current_state.section_number)
                transitions = await self.get_available_transitions(current_state)

                # 2. Update state with available transitions
                logger.debug("Updating state with available transitions")
                current_state.available_transitions = transitions
                yield current_state

                # 3. Check if workflow should continue
                if not transitions:
                    logger.info("No more transitions available, stopping workflow")
                    break

        except Exception as e:
            logger.error("Error streaming workflow: {}", str(e), exc_info=True)
            raise WorkflowError(f"Failed to stream workflow: {str(e)}")

    async def handle_error(self, error: Exception) -> GameState:
        """Handle workflow error.

        Args:
            error: Error to handle

        Returns:
            GameState: Error state
        """
        try:
            logger.error("Handling workflow error: {}", str(error))
            error_message = str(error)
            if isinstance(error, WorkflowError):
                error_message = f"Workflow error: {error_message}"
            return await self.state_manager.create_error_state(error_message)

        except Exception as e:
            logger.error("Error handling workflow error: {}", str(e), exc_info=True)
            return await self.state_manager.create_error_state(str(e))

    async def execute_workflow(
        self,
        state: Optional[GameState] = None,
        user_input: Optional[str] = None,
        story_graph: Optional[StoryGraphProtocol] = None
    ) -> GameState:
        """Execute game workflow.

        Args:
            state: Optional game state to use
            user_input: Optional user input
            story_graph: Optional StoryGraph instance to use

        Returns:
            GameState: Updated game state

        Raises:
            WorkflowError: If workflow execution fails
        """
        try:
            logger.info("Starting workflow execution")
            logger.debug("Input state: {}, User input: {}", state, user_input)

            if not state:
                state = await self.state_manager.get_current_state()
                if not state:
                    raise WorkflowError("No current state available")

            if not story_graph:
                raise WorkflowError("No story graph provided")

            # Setup and compile workflow
            logger.debug("Setting up and compiling workflow")
            workflow = await story_graph.get_compiled_workflow()

            # Create input for story graph using with_updates to preserve session_id
            input_data = state.with_updates(
                player_input=user_input,
                section_number=state.section_number,
                content=state.narrative_content if hasattr(state, 'narrative_content') else None
            )

            # Execute workflow
            logger.debug("Executing workflow")
            # Pass GameState directly to workflow
            async for result in workflow.astream(input_data):
                logger.debug(f"Workflow execution result: {result}")
                if isinstance(result, GameState):
                    # Save state
                    logger.debug("Saving new state")
                    await self.state_manager.save_state(result)
                    logger.info("Workflow execution completed successfully")
                    return result
                
            logger.error("No valid result from workflow")
            raise WorkflowError("No valid result from workflow execution")

        except Exception as e:
            logger.error("Error executing workflow: {}", str(e), exc_info=True)
            raise WorkflowError(f"Failed to execute workflow: {str(e)}")

    # Méthode modifiée sans création manuelle de session_id
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

            # Validation que le `session_id` est présent dans l'état
            if not getattr(state, "session_id", None):
                logger.debug("Creating initial state with session_id")
                state = await self.state_manager.create_initial_state()
            logger.debug("Validated state session_id: {}", state.session_id)

            # Création de la sortie avec métadonnées en utilisant with_updates
            output = state.with_updates(
                metadata={"node": "start"},
                section_number=max(1, state.section_number)  # Ensure section_number is at least 1
            )

            logger.info("Successfully created output with session_id: {}", output.session_id)
            return output

        except Exception as e:
            logger.error("Error during start_workflow: {}", str(e), exc_info=True)
            raise WorkflowError(f"Failed to start workflow: {str(e)}")

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
                       output_data.state.section_number if output_data.state else None)

            # Save final state if present
            if output_data.state:
                logger.debug("Saving final state")
                output_data.state = await self.state_manager.save_state(output_data.state)

            logger.info("Workflow ended successfully")
            return output_data

        except Exception as e:
            logger.error("Error in end node: {}", str(e), exc_info=True)
            return GameState(
                state=await self.state_manager.create_error_state(str(e)),
                error=str(e)
            )

    async def initialize_workflow(self, initial_state: GameState) -> None:
        """Initialize workflow with initial state.

        Args:
            initial_state: Initial game state to use

        Raises:
            WorkflowError: If initialization fails
        """
        try:
            logger.info("Initializing workflow")
            logger.debug(f"Initial state: {initial_state}")

            # Save initial state
            logger.debug("Saving initial state")
            await self.state_manager.save_state(initial_state)

            logger.info("Workflow initialization completed")

        except Exception as e:
            logger.error(f"Error initializing workflow: {e}", exc_info=True)
            raise WorkflowError(f"Failed to initialize workflow: {str(e)}")