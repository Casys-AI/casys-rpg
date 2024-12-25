"""
Story Graph Agent
"""
from typing import Dict, Any, Optional, AsyncGenerator, List, Annotated
from loguru import logger
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolExecutor

from agents.protocols.story_graph_protocol import StoryGraphProtocol
from managers.protocols.workflow_manager_protocol import WorkflowManagerProtocol
from managers.protocols.state_manager_protocol import StateManagerProtocol
from models.game_state import GameState
from models.errors_model import GameError, NarratorError, RulesError
from config.agents.agent_config_base import AgentConfigBase
from agents.factories.game_factory import GameAgents, GameManagers


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

            if self.rules_agent:
                # Process rules directly through the agent
                rules = await self.rules_agent.process_section_rules(
                    input_data.section_number,
                    input_data.content
                )
                
                if isinstance(rules, RulesError):
                    raise rules
                
                output = GameState(
                    session_id=input_data.session_id,
                    rules=rules,
                    narrative_content=input_data.content,
                    section_number=input_data.section_number,
                )
                logger.debug("Rules processing completed for section {}", input_data.section_number)
                return output

            logger.debug("No rules agent available, returning empty output")
            return GameState(session_id=input_data.session_id)
        except Exception as e:
            logger.exception("Error processing rules: {}", str(e))
            return GameState(
                session_id=input_data.session_id,
                error=str(e)
            )

    async def _process_narrative(self, input_data: GameState) -> GameState:
        """Process narrative for the current state."""
        try:
            logger.info("Processing narrative for section {}", input_data.section_number)
            
            if not input_data:
                raise GameError("No input data available for narrative processing")

            if self.narrator_agent:
                # Process narrative through the agent
                narrator_result = await self.narrator_agent.process_section(
                    input_data.section_number,
                    input_data.content
                )
                
                if isinstance(narrator_result, NarratorError):
                    raise narrator_result
                
                output = GameState(
                    session_id=input_data.session_id,
                    narrative=narrator_result,
                    narrative_content=input_data.content,
                    section_number=input_data.section_number,
                )
                logger.debug("Narrative processing completed for section {}", input_data.section_number)
                return output

            logger.debug("No narrator agent available, returning empty output")
            return GameState(session_id=input_data.session_id)
        except Exception as e:
            logger.exception("Error processing narrative: {}", str(e))
            return GameState(
                session_id=input_data.session_id,
                error=str(e)
            )


    async def _process_decision(
        self,
        state: GameState
    ) -> GameState:
        """Merge results from parallel states and process decision."""
        try:
            logger.info("Processing decision with merged state")

            # Vérifier si les données nécessaires sont présentes
            rules_data = state.rules
            narrative_data = state.narrative

            if not rules_data or not narrative_data:
                raise GameError("Missing required data for decision processing")

            # Loguer les données reçues pour débogage
            logger.debug(f"Rules Data: {rules_data}")
            logger.debug(f"Narrative Data: {narrative_data}")

            # Fusion des données (exemple : prioriser les données des règles)
            final_state = GameState(
                session_id=state.session_id,
                rules=rules_data,
                narrative=narrative_data,
                decision=None,  # Initialement vide, à mettre à jour après analyse
                error=None
            )

            # Processus de décision via l'agent de décision
            if self.decision_agent:
                decision = await self.decision_agent.analyze_decision(final_state)
                final_state.decision = decision
                logger.info("Decision processed successfully")

            else:
                logger.warning("No decision agent available, returning merged state as is")

            return final_state

        except Exception as e:
            logger.exception("Error processing decision: {}", str(e))
            return GameState(
                session_id=state.session_id,
                error=str(e)
            )


    async def _process_trace(self, input_data: GameState) -> GameState:
        """Process trace for the current state."""
        try:
            logger.info("Processing trace for section {}", input_data.section_number)
            
            if not input_data:
                raise GameError("No input data available for trace processing")

            if self.trace_agent:
                # Record state
                trace = await self.trace_agent.record_state(input_data)
                
                # Analyze state
                state = await self.trace_agent.analyze_state(input_data)
                
                return GameState(
                    session_id=input_data.session_id,
                    trace=trace,
                    section_number=input_data.section_number,
                    source=input_data.source,
                )

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
