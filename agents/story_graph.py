"""
Story Graph Agent
"""
from typing import Dict, Any, Optional, AsyncGenerator, List, Annotated
from loguru import logger
from pydantic import BaseModel, Field

from models.game_state import GameState
from models.errors_model import (
    GameError,
    NarratorError,
    RulesError,
    DecisionError,
    TraceError
)
from models.narrator_model import NarratorModel
from models.decision_model import DecisionModel
from models.rules_model import RulesModel
from models.trace_model import TraceModel
from models.types.agent_types import GameAgents
from models.types.manager_types import GameManagers
from config.agents.agent_config_base import AgentConfigBase

from agents.protocols.story_graph_protocol import StoryGraphProtocol
from managers.protocols.workflow_manager_protocol import WorkflowManagerProtocol
from managers.protocols.state_manager_protocol import StateManagerProtocol
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolExecutor


class StoryGraph(StoryGraphProtocol):
    """Story Graph implementation for managing game workflow using LangGraph."""

    def __init__(
        self,
        config: AgentConfigBase,
        managers: GameManagers,
        agents: Optional[GameAgents] = None
    ):
        """Initialize StoryGraph.
        
        Args:
            config: Configuration for the story graph
            managers: Container with all game managers
            agents: Optional container with all game agents
        """
        # Initialize managers
        self.state_manager = managers.state_manager
        self.workflow_manager = managers.workflow_manager
        self.rules_manager = managers.rules_manager
        self.narrator_manager = managers.narrator_manager
        self.decision_manager = managers.decision_manager
        self.trace_manager = managers.trace_manager
        
        # Initialize agents if provided
        if agents:
            self.rules_agent = agents.rules_agent
            self.narrator_agent = agents.narrator_agent
            self.decision_agent = agents.decision_agent
            self.trace_agent = agents.trace_agent
        
        self._graph = None
        self._current_section = 1

    async def _setup_workflow(self) -> None:
        try:
            logger.info("Setting up LangGraph workflow with parallel processing")

            self._graph = StateGraph(GameState, output=GameState)

            # Ajouter les nœuds
            self._graph.add_node("node_start", self.workflow_manager.start_workflow)
            self._graph.add_node("node_rules", self._process_rules)
            self._graph.add_node("node_narrator", self._process_narrative)
            self._graph.add_node("node_decision", self._process_decision)
            self._graph.add_node("node_end", self.workflow_manager.end_workflow)

            # Ajouter les connexions
            self._graph.add_edge(START, "node_start")
            self._graph.add_edge("node_start", "node_rules")
            self._graph.add_edge("node_start", "node_narrator")

            # Fan-in : fusion des résultats de `rules` et `narrator` dans `decision`
            self._graph.add_edge(["node_rules", "node_narrator"], "node_decision")

            # Fin du workflow
            self._graph.add_edge("node_decision", "node_end")
            self._graph.add_edge("node_end", END)

            # Compiler le graphe
            self._graph.compile()
            logger.success("Workflow setup completed")
        except Exception as e:
            logger.exception("Error setting up workflow: {}", str(e))
            raise




    async def _process_rules(self, input_data: GameState) -> GameState:
        """Process game rules for the current state."""
        try:
            logger.info("Processing rules for section {}", input_data.section_number)
            
            if not input_data:
                raise GameError("No input data available for rules processing")

            if not self.rules_agent:
                logger.debug("No rules agent available, returning input state")
                return input_data

            async for result in self.rules_agent.ainvoke({"state": input_data}):
                if "rules" in result:
                    rules = result["rules"]
                    if isinstance(rules, RulesError):
                        raise rules
                    
                    output = input_data.with_updates(rules=rules)
                    logger.debug("Rules processing completed for section {}", 
                               input_data.section_number)
                    return output
                    
            raise GameError("No valid rules result")
            
        except Exception as e:
            logger.exception("Error processing rules: {}", str(e))
            return GameState(
                session_id=input_data.session_id,
                game_id=input_data.game_id,
                section_number=input_data.section_number,
                error=str(e)
            )

    async def _process_narrative(self, input_data: GameState) -> GameState:
        """Process narrative for the current state."""
        try:
            logger.info("Processing narrative for section {}", input_data.section_number)
            
            if not input_data:
                raise GameError("No input data available for narrative processing")

            if not self.narrator_agent:
                logger.debug("No narrator agent available, returning input state")
                return input_data

            # Process narrative through the agent
            async for result in self.narrator_agent.ainvoke({"state": input_data}):
                if "narrative" in result:
                    narrator_result = result["narrative"]
                    if isinstance(narrator_result, NarratorError):
                        raise narrator_result
                    
                    output = input_data.with_updates(
                        narrative=narrator_result,
                        narrative_content=input_data.content
                    )
                    logger.debug("Narrative processing completed for section {}", 
                               input_data.section_number)
                    return output

            raise GameError("No valid narrative result")

        except Exception as e:
            logger.exception("Error processing narrative: {}", str(e))
            return GameState(
                session_id=input_data.session_id,
                game_id=input_data.game_id,
                section_number=input_data.section_number,
                error=str(e)
            )


    async def _process_decision(
        self,
        state: GameState
    ) -> GameState:
        """Process decision node."""
        try:
            if not self.decision_agent:
                logger.debug("No decision agent available, returning input state")
                return state

            if state.player_input:
                logger.debug("Processing user input: {}", state.player_input)
                async for result in self.decision_agent.ainvoke({"state": state}):
                    if "decision" in result:
                        decision = result["decision"]
                        if isinstance(decision, DecisionError):
                            logger.error("Decision error: {}", decision.message)
                            return GameState(
                                session_id=state.session_id,
                                game_id=state.game_id,
                                section_number=state.section_number,
                                error=decision.message
                            )
                        
                        # Vérifier que next_section est présent dans la décision
                        if not hasattr(decision, 'next_section') or decision.next_section is None:
                            logger.error("Decision missing next_section")
                            return GameState(
                                session_id=state.session_id,
                                game_id=state.game_id,
                                section_number=state.section_number,
                                error="Decision missing next section number"
                            )
                        
                        output = state.with_updates(decision=decision)
                        logger.debug("Decision processed: next_section={}", decision.next_section)
                        return output

                raise GameError("No valid decision result")

            logger.debug("No user input to process")
            if state.rules and state.rules.needs_user_response:
                logger.info(" En attente d'une réponse utilisateur pour la section {}", state.section_number)
            return state

        except Exception as e:
            logger.exception("Error in decision processing: {}", str(e))
            return GameState(
                session_id=state.session_id,
                game_id=state.game_id,
                section_number=state.section_number,
                error=str(e)
            )


    async def _process_trace(self, input_data: GameState) -> GameState:
        """Process trace for the current state."""
        try:
            logger.info("Processing trace for section {}", input_data.section_number)
            
            if not input_data:
                raise GameError("No input data available for trace processing")

            if self.trace_agent:
                async for result in self.trace_agent.ainvoke({"state": input_data}):
                    if "trace" in result:
                        trace = result["trace"]
                        if isinstance(trace, TraceError):
                            raise trace
                        
                        output = input_data.with_updates(trace=trace)
                        logger.debug("Trace processing completed for section {}", 
                                   input_data.section_number)
                        return output
                        
                raise GameError("No valid trace result")

            logger.debug("No trace agent available, returning empty output")
            return GameState(session_id=input_data.session_id)
            
        except Exception as e:
            logger.exception("Error processing trace: {}", str(e))
            return GameState(
                session_id=input_data.session_id,
                error=str(e)
            )

    async def get_compiled_workflow(self) -> Any:
        """Get the compiled workflow graph.
        
        Returns:
            Any: Compiled workflow graph ready for execution
        """
        if not self._graph:
            await self._setup_workflow()
        return self._graph.compile()
