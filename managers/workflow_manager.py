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
        """Start the workflow node (improved version)."""
        try:
            logger.info("Starting workflow node (improved version)")
            logger.debug("Input data received: Type: {}, Value: {}", type(input_data), input_data)

            # Initialize state manager first
            await self.state_manager.initialize()

            if not input_data:
                logger.error("No input data provided")
                raise WorkflowError("No input data provided")

            # 1) Convertir en dict si c'est déjà un GameState
            if isinstance(input_data, GameState):
                logger.debug("Input is already a GameState, converting to dict")
                input_data = input_data.model_dump(exclude_unset=False)

            if not isinstance(input_data, dict):
                logger.error("Invalid input data type: {}. Expected GameState or dict.", type(input_data))
                raise WorkflowError(f"Invalid input data type: {type(input_data)}. Expected GameState or dict.")

            # 2) Vérifier session_id / game_id
            has_session = bool(input_data.get("session_id"))
            has_game = bool(input_data.get("game_id"))
            logger.debug("Input data has session_id: {}, game_id: {}", has_session, has_game)

            if not has_session or not has_game:
                logger.info("No valid session_id/game_id found, creating initial state")
                initial_state = await self.state_manager.create_initial_state()
                logger.debug("Initial state created: session_id={}, game_id={}", initial_state.session_id, initial_state.game_id)

                # Fusionner les données d'entrée avec l'état initial sans écraser les IDs existants
                merged_data = initial_state.model_dump(exclude_unset=False)
                logger.debug("Initial merged data: session_id={}, game_id={}", merged_data.get("session_id"), merged_data.get("game_id"))

                for key, value in input_data.items():
                    if key not in merged_data or not merged_data[key]:
                        merged_data[key] = value

                input_data = merged_data
                logger.debug("Merged input data after preserving IDs: session_id={}, game_id={}", 
                            input_data.get("session_id"), input_data.get("game_id"))

            else:
                logger.debug("Existing session_id and game_id found: session_id={}, game_id={}", 
                            input_data.get("session_id"), input_data.get("game_id"))

            # 3) Gérer next_section → section_number
            if "next_section" in input_data and input_data["next_section"] is not None:
                logger.info("Found next_section={}, converting to section_number", input_data["next_section"])
                input_data["section_number"] = input_data.pop("next_section")
                logger.debug("Updated section_number to {}", input_data["section_number"])

            # 4) Construire le GameState final
            #    (Si session_id/game_id sont présents, ils sont déjà dans input_data)
            state = GameState(**input_data)
            logger.debug("Constructed GameState: session_id={}, game_id={}, section_number={}", 
                        state.session_id, state.game_id, state.section_number)

            # 5) Ajouter métadonnées
            state = state.with_updates(metadata={"node": "start"})
            logger.debug("Added metadata to GameState: {}", state.metadata)

            # 6) Sauvegarder
            saved_state = await self.state_manager.save_state(state)
            logger.debug("Saved State: session_id={}, game_id={}, section_number={}", 
                        saved_state.session_id, saved_state.game_id, saved_state.section_number)
            logger.info(
                "Successfully created and saved output with session_id: {} and section_number: {}",
                saved_state.session_id,
                saved_state.section_number
            )

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