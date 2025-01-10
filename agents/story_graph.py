"""
Story Graph Agent
"""
from typing import Dict, Any, Optional, AsyncGenerator, List, Union
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

from config.agents.agent_config_base import AgentConfigBase

from agents.protocols.story_graph_protocol import StoryGraphProtocol
from agents.protocols.rules_agent_protocol import RulesAgentProtocol
from agents.protocols.narrator_agent_protocol import NarratorAgentProtocol
from agents.protocols.decision_agent_protocol import DecisionAgentProtocol
from agents.protocols.trace_agent_protocol import TraceAgentProtocol

from managers.protocols.workflow_manager_protocol import WorkflowManagerProtocol
from managers.protocols.state_manager_protocol import StateManagerProtocol

from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolExecutor
from langgraph.types import Command, interrupt  
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import GraphInterrupt

# Type alias for manager protocols
ManagerProtocols = Union[
    WorkflowManagerProtocol,
    StateManagerProtocol
]

class StoryGraph(StoryGraphProtocol):
    """Story Graph implementation for managing game workflow using LangGraph."""

    def __init__(
        self,
        config: AgentConfigBase,
        managers: Dict[str, ManagerProtocols],
        agents: Optional[Dict[str, Union[
            NarratorAgentProtocol,
            RulesAgentProtocol,
            DecisionAgentProtocol,
            TraceAgentProtocol
        ]]] = None
    ):
        """Initialize StoryGraph.
        
        Args:
            config: Configuration for the story graph
            managers: Container with all game managers
            agents: Optional container with all game agents
        """
        # Initialize managers
        self.state_manager: StateManagerProtocol = managers["state_manager"]
        self.workflow_manager: WorkflowManagerProtocol = managers["workflow_manager"]
        
        # Initialize agents
        if agents:
            self.rules_agent: RulesAgentProtocol = agents["rules_agent"]
            self.narrator_agent: NarratorAgentProtocol = agents["narrator_agent"]
            self.decision_agent: DecisionAgentProtocol = agents["decision_agent"]
            self.trace_agent: TraceAgentProtocol = agents["trace_agent"]
        
        self._graph = None
        self._memory = None

    async def _setup_workflow(self) -> None:
        try:
            logger.info("Setting up LangGraph workflow with parallel processing")

            self._graph = StateGraph(GameState, output=GameState)

            # Ajouter les nœuds
            self._graph.add_node("node_start", self.workflow_manager.start_workflow)

            self._graph.add_node("node_narrator", self._process_narrative)
            self._graph.add_node("node_rules", self._process_rules)
            self._graph.add_node("node_decision", self._process_decision)
            #self._graph.add_node("node_trace", self._process_trace)  # Ajouté pour la traçabilité
            self._graph.add_node("node_end", self.workflow_manager.end_workflow)

            # Ajouter les connexions
            self._graph.add_edge(START, "node_start")
            self._graph.add_edge("node_start", "node_narrator")
            self._graph.add_edge("node_start", "node_rules")


            # Fan-in : fusion des résultats de `rules` et `narrator` dans `decision`
            self._graph.add_edge(["node_rules", "node_narrator"], "node_decision")
            
            # Ajouter une connexion conditionnelle basée sur `should_continue`
            def should_continue_condition(state):
                logger.debug("Condition state details: {}", state.model_dump())
                logger.info("[WORKFLOW] Evaluating should_continue={} for section {}", 
                          state.should_continue, state.section_number)
                return state.should_continue

            self._graph.add_conditional_edges(
                "node_decision",
                should_continue_condition,
                {True: "node_start", False: "node_end"}
            )
            #self._graph.add_edge("node_trace", "node_end")
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

            # Process rules through the agent
            async for result in self.rules_agent.ainvoke({"state": input_data}):
                if "rules" in result:
                    rules_result = result["rules"]
                    if isinstance(rules_result, RulesError):
                        raise rules_result
                        
                    logger.debug("Received rules from agent: {}", rules_result)
                    output = input_data.with_node_updates('node_rules', rules=rules_result)
                    return output
                    
            raise GameError("No valid rules result")
            
        except Exception as e:
            logger.exception("Error processing rules: {}", str(e))
            error_state = input_data.with_updates(error=str(e))
            return error_state

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
                    
                    logger.debug("Received narrative content from agent: {}", 
                               (narrator_result.content[:100] + "...") if len(narrator_result.content) > 100 else narrator_result.content)
                    output = input_data.with_node_updates('node_narrator', narrative=narrator_result)
                    return output

            raise GameError("No valid narrative result")
        except Exception as e:
            logger.exception("Error processing narrative: {}", str(e))
            error_state = input_data.with_updates(error=str(e))
            return error_state


    async def _process_decision(self, input_data: GameState) -> GameState:
        """Process decision node."""
        try:
            # Essayer d'extraire le player_input en premier
            response = None
            if isinstance(input_data, Command):
                logger.debug("[DECISION] Received Command with resume={} (type={})", 
                           input_data.resume, type(input_data.resume))
                # Extraire le player_input du dict
                if isinstance(input_data.resume, dict) and "player_input" in input_data.resume:
                    response = input_data.resume["player_input"]
                else:
                    response = input_data.resume
            else:
                # Si on a besoin d'une réponse utilisateur
                if input_data.rules and input_data.rules.needs_user_response:
                    logger.info("Waiting for user input in section {}", input_data.section_number)
                    response = interrupt("[DECISION] Waiting for user input")
                    logger.debug("[DECISION] Received interrupt response: {} (type={})", response, type(response))

            # Extraire le player_input si présent
            user_input = None
            has_player_input = False
            if response:
                if isinstance(response, dict) and "player_input" in response:
                    user_input = response["player_input"]
                    has_player_input = True
                    logger.debug("[DECISION] Extracted player_input from dict: {}", user_input)
                elif isinstance(response, str):
                    user_input = response
                    has_player_input = True
                    logger.debug("[DECISION] Using response directly as user_input: {}", user_input)

            # Créer ou mettre à jour le DecisionModel
            if has_player_input:
                input_data = input_data.with_node_updates('node_decision', decision=DecisionModel(
                    section_number=input_data.section_number,
                    next_section=None,
                    player_input=user_input
                ))
            elif not input_data.decision:
                logger.debug("[DECISION] Creating initial DecisionModel")
                input_data = input_data.with_node_updates('node_decision', decision=DecisionModel(
                    section_number=input_data.section_number,
                    next_section=None,
                    player_input=None
                ))

            logger.info("[DECISION] Processing decision for section {} (cycle {})", 
                       input_data.section_number if input_data else None,
                       "with_input" if has_player_input else "initial")

            if not input_data:
                raise GameError("No input data available for decision processing")

            if not self.decision_agent:
                logger.debug("No decision agent available, returning input state")
                return input_data

            # Debug player input
            logger.debug("[DECISION] Current player_input value: {}, section_number={}", 
                        input_data.decision.player_input if input_data.decision else None,
                        input_data.section_number)
            logger.debug("[DECISION] Input data rules: needs_user_response={}, has_player_input={}", 
                        input_data.rules.needs_user_response if input_data.rules else None,
                        bool(input_data.decision and input_data.decision.player_input))

            # Si on n'a pas besoin d'input utilisateur, on continue le workflow
            if input_data.rules and not input_data.rules.needs_user_response:
                logger.info("[DECISION] No user input needed, continuing workflow")
                # Mettre à jour should_continue pour continuer le workflow
                input_data = input_data.with_updates(should_continue=True)

            # Processus de décision si on a un player_input
            if input_data.decision and input_data.decision.player_input:
                logger.info("[DECISION] Processing decision with input: {}", input_data.decision.player_input)
                # Appeler le decision agent avec ainvoke
                async for decision_output in self.decision_agent.ainvoke({"state": input_data}):
                    decision = decision_output.get("decision")
                    logger.debug("[DECISION] Decision result: {}", decision)

                    if isinstance(decision, DecisionError):
                        logger.error("Decision error: {}", decision.message)
                        return input_data.with_updates(error=decision.message, decision=None, should_continue=False)

                    if (not hasattr(decision, 'next_section') or decision.next_section is None) and not hasattr(decision, 'awaiting_action'):
                        logger.error("Decision missing next_section or awaiting_action")
                        return input_data.with_updates(error="Decision missing next_section or awaiting_action", decision=None, should_continue=False)

                    logger.info("Decision processed: current_section={}, next_section={}", 
                            input_data.section_number, decision.next_section)
                    
                    # Utiliser with_node_updates pour le DecisionModel
                    return input_data.with_node_updates('node_decision', decision=decision).with_updates(should_continue=True)

            logger.debug("No user input to process")
            # Pas de should_continue=False ici car on veut garder la valeur précédente
            return input_data

        except GraphInterrupt as gi:
            logger.info("Workflow interrupted for user input: {}", gi)
            raise gi  # Propager l'interruption

        except Exception as e:
            logger.exception("Error processing decision: {}", str(e))
            error_state = input_data.with_updates(error=str(e))
            return error_state

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

            logger.debug("No trace agent available, returning input state")
            return input_data

        except Exception as e:
            logger.exception("Error processing trace: {}", str(e))
            return input_data.with_updates(error=str(e))

    async def get_compiled_workflow(self) -> Any:
        """Get the compiled workflow graph.
        
        Returns:
            Any: Compiled workflow graph ready for execution
        """
        self._memory = MemorySaver()
        if not self._graph:
            await self._setup_workflow()
        return self._graph.compile(checkpointer=self._memory)

# Register protocol implementation
StoryGraphProtocol.register(StoryGraph)
