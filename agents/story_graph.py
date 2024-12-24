"""
Story Graph Agent
"""
from typing import Dict, Any, Optional, AsyncGenerator, List
from loguru import logger
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolExecutor

from agents.protocols.story_graph_protocol import StoryGraphProtocol
from managers.protocols.workflow_manager_protocol import WorkflowManagerProtocol
from managers.protocols.state_manager_protocol import StateManagerProtocol
from models.game_state import GameState, GameStateInput, GameStateOutput
from models.errors_model import GameError, NarratorError
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
        """Configure LangGraph workflow with parallel processing for rules and narrative."""
        try:
            logger.info("Setting up LangGraph workflow with parallel processing")
            
            # Create StateGraph with input/output models
            self._graph = StateGraph(GameStateInput, output=GameStateOutput)
            logger.debug("Created StateGraph with models")
            
            # Define node names
            START_NODE = "node_start"
            RULES_NODE = "node_rules"
            NARRATOR_NODE = "node_narrator"
            DECISION_NODE = "node_decision"
            TRACE_NODE = "node_trace"
            END_NODE = "node_end"
            
            logger.debug("Adding workflow nodes")
            # Add workflow nodes
            self._graph.add_node(START_NODE, self.workflow_manager.start_workflow)
            self._graph.add_node(RULES_NODE, self._process_rules)
            self._graph.add_node(NARRATOR_NODE, self._process_narrative)
            self._graph.add_node(DECISION_NODE, self._process_decision)
            self._graph.add_node(TRACE_NODE, self._process_trace)
            self._graph.add_node(END_NODE, self.workflow_manager.end_workflow)
            
            logger.debug("Defining conditional routing functions")
            # Define conditional routing based on state
            def route_to_parallel(state: GameStateInput) -> List[str]:
                """Route to both rules and narrator nodes."""
                logger.debug("Routing to parallel nodes: {}, {}", RULES_NODE, NARRATOR_NODE)
                return [RULES_NODE, NARRATOR_NODE]
                
            self.route_after_parallel = lambda state: self._route_after_parallel(state)
            
            logger.debug("Setting up workflow edges")
            # Define workflow edges with parallel processing
            self._graph.add_edge(START, START_NODE)
            
            # Start parallel processing
            self._graph.add_conditional_edges(
                START_NODE,
                route_to_parallel
            )
            
            # Wait for both processes to complete
            self._graph.add_conditional_edges(
                RULES_NODE,
                self.route_after_parallel
            )
            self._graph.add_conditional_edges(
                NARRATOR_NODE,
                self.route_after_parallel
            )
            
            # Continue with sequential flow
            self._graph.add_edge(DECISION_NODE, TRACE_NODE)
            self._graph.add_edge(TRACE_NODE, END_NODE)
            self._graph.add_edge(END_NODE, END)
            
            # Compile graph
            logger.debug("Compiling workflow graph")
            self._graph.compile()
            
            logger.success("LangGraph workflow setup completed successfully")
            
        except Exception as e:
            logger.exception("Error setting up LangGraph workflow: {}", str(e))
            raise

    async def _process_rules(self, input_data: GameStateInput) -> GameStateOutput:
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
                
                output = GameStateOutput(
                    session_id=input_data.session_id,
                    rules=rules,
                    narrative_content=input_data.content,
                    section_number=input_data.section_number,
                    source=input_data.source
                )
                logger.debug("Rules processing completed for section {}", input_data.section_number)
                return output

            logger.debug("No rules agent available, returning empty output")
            return GameStateOutput(session_id=input_data.session_id)
        except Exception as e:
            logger.exception("Error processing rules: {}", str(e))
            return GameStateOutput(
                session_id=input_data.session_id,
                error=str(e)
            )

    async def _process_narrative(self, input_data: GameStateInput) -> GameStateOutput:
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
                
                output = GameStateOutput(
                    session_id=input_data.session_id,
                    narrative=narrator_result,
                    narrative_content=input_data.content,
                    section_number=input_data.section_number,
                    source=input_data.source
                )
                logger.debug("Narrative processing completed for section {}", input_data.section_number)
                return output

            logger.debug("No narrator agent available, returning empty output")
            return GameStateOutput(session_id=input_data.session_id)
        except Exception as e:
            logger.exception("Error processing narrative: {}", str(e))
            return GameStateOutput(
                session_id=input_data.session_id,
                error=str(e)
            )

    def _route_after_parallel(self, state: Any) -> Optional[List[str]]:
        """Route to decision after both processes complete."""
        logger.debug("Checking parallel processes completion")
        
        # Log state details at trace level for debugging
        logger.trace("Received state: type={}, content={}", 
                    type(state).__name__,
                    state.__dict__ if hasattr(state, '__dict__') else str(state))

        # Si c'est un GameStateInput, on continue avec les deux branches
        if isinstance(state, GameStateInput):
            logger.debug("GameStateInput received, continuing parallel processing")
            return ["node_rules", "node_narrator"]

        # Si c'est un GameStateOutput, on vérifie qu'on a les deux résultats
        if isinstance(state, GameStateOutput):
            if state.rules is not None and state.narrative is not None:
                logger.info("Both parallel processes complete, routing to decision node")
                return ["node_decision"]
            
            logger.debug("Waiting for parallel processes to complete: rules={}, narrative={}", 
                      state.rules is not None, 
                      state.narrative is not None)
            return ["node_rules", "node_narrator"]  # Continue parallel processing

        # Pour tout autre type d'état, on continue le traitement parallèle
        logger.warning("Unexpected state type in parallel routing: {}, continuing parallel processing", type(state).__name__)
        return ["node_rules", "node_narrator"]

    async def _process_decision(self, input_data: GameStateInput) -> GameStateOutput:
        """Process decision for the current state."""
        try:
            logger.info("Processing decision for section {}", input_data.section_number)
            
            if not input_data:
                raise GameError("No input data available for decision processing")

            if self.decision_agent:
                # Analyze decision
                state = GameState(
                    section_number=input_data.section_number,
                    player_input=input_data.player_input,
                    content=input_data.content,
                    source=input_data.source,
                    session_id=input_data.session_id
                )
                updated_state = await self.decision_agent.analyze_decision(state)
                
                return GameStateOutput(
                    decision=updated_state.decision,
                    section_number=updated_state.section_number,
                    source=updated_state.source,
                    session_id=updated_state.session_id
                )

            logger.debug("No decision agent available, returning empty output")
            return GameStateOutput(session_id=input_data.session_id)
        except Exception as e:
            logger.exception("Error processing decision: {}", str(e))
            return GameStateOutput(
                session_id=input_data.session_id,
                error=str(e)
            )

    async def _process_trace(self, input_data: GameStateInput) -> GameStateOutput:
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
                
                return GameStateOutput(
                    trace=trace,
                    section_number=input_data.section_number,
                    source=input_data.source,
                    session_id=input_data.session_id
                )

            logger.debug("No trace agent available, returning empty output")
            return GameStateOutput(session_id=input_data.session_id)
        except Exception as e:
            logger.exception("Error processing trace: {}", str(e))
            return GameStateOutput(
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
