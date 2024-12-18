"""
Story Graph Module
Handles game workflow and progression.
"""

from typing import Dict, Optional, AsyncGenerator, Any
from pydantic import Field, ConfigDict

from agents.base_agent import BaseAgent
from models.game_state import GameState
from models.narrator_model import NarratorModel
from models.rules_model import RulesModel
from models.trace_model import TraceModel
from models.decision_model import DecisionModel
from config.agent_config import AgentConfig
from config.logging_config import get_logger
from agents.protocols import StoryGraphProtocol
from agents.narrator_agent import NarratorAgent
from agents.rules_agent import RulesAgent
from agents.decision_agent import DecisionAgent
from agents.trace_agent import TraceAgent
from managers.state_manager import StateManager
from managers.trace_manager import TraceManager
from langgraph.graph import StateGraph, END
from managers.cache_manager import CacheManager

logger = get_logger('story_graph')

class StoryGraph(BaseAgent, StoryGraphProtocol):
    """Agent responsible for managing game workflow and progression."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Configuration de base
    config: AgentConfig = Field(default_factory=AgentConfig)
    
    # Composants requis
    narrator: NarratorAgent
    rules: RulesAgent
    decision: DecisionAgent
    trace: TraceAgent
    state_manager: StateManager
    trace_manager: TraceManager
    
    # État interne
    _graph: Optional[StateGraph] = None

    def __init__(
        self,
        config: AgentConfig,
        cache_manager: CacheManager,
        narrator: NarratorAgent,
        rules: RulesAgent,
        decision: DecisionAgent,
        trace: TraceAgent,
        state_manager: StateManager,
        trace_manager: TraceManager,
        **data
    ):
        """Initialize StoryGraph with all required components."""
        super().__init__(config=config, cache_manager=cache_manager)
        self.narrator = narrator
        self.rules = rules
        self.decision = decision
        self.trace = trace
        self.state_manager = state_manager
        self.trace_manager = trace_manager

    async def _process_with_agent(self, agent: Any, state: Dict) -> AsyncGenerator[Dict, None]:
        """Process state with an agent."""
        result = await agent.process(state)
        yield result

    def _merge_parallel_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Merge results from parallel agent executions."""
        try:
            section = results.get("narrator", {})
            rules = results.get("rules", {})
            return {
                "section": section,
                "rules": rules,
                "state": GameState(
                    current_section=section,
                    current_rules=rules
                )
            }
        except Exception as e:
            logger.error(f"Error merging results: {e}")
            raise

    async def _initialize_state(self, state: Dict) -> Dict:
        """Initialize and validate game state.
        
        Args:
            state: Initial state dict
            
        Returns:
            Validated GameState
        """
        logger.debug("Initializing game state")
        
        try:
            # Create initial state
            initial_state = GameState.create_initial_state()
            
            # Process with agents
            narrator_result = await self.narrator.process(initial_state.model_dump())
            rules_result = await self.rules.process(initial_state.model_dump())
            
            # Merge results
            merged = self._merge_parallel_results({
                "narrator": narrator_result,
                "rules": rules_result
            })
            
            return merged
            
        except Exception as e:
            logger.error(f"Error initializing state: {e}")
            return self.state_manager.create_error_state(str(e))

    def _setup_workflow(self) -> None:
        """Setup the story graph workflow."""
        if self._graph is not None:
            return

        logger.debug("Setting up story graph workflow")
        workflow = StateGraph({})

        # Add start node for initialization
        workflow.add_node("start", self._initialize_state)

        # Add nodes for each agent
        workflow.add_node("narrator", lambda x: self._process_with_agent(self.narrator, x))
        workflow.add_node("rules", lambda x: self._process_with_agent(self.rules, x))
        workflow.add_node("decision", lambda x: self._process_with_agent(self.decision, x))
        workflow.add_node("trace", lambda x: self._process_with_agent(self.trace, x))

        # Configure parallel execution
        workflow.add_node("merge", self._merge_parallel_results)
        
        # Define workflow edges
        workflow.add_edge("start", "narrator")  # Start -> Narrator
        workflow.add_edge("narrator", "rules")  # Narrator -> Rules
        workflow.add_edge("rules", "decision")  # Rules -> Decision
        workflow.add_edge("decision", "trace")  # Decision -> Trace
        workflow.add_edge("trace", END)         # Trace -> End

        self._graph = workflow

    async def _process_workflow(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process state through the workflow."""
        if not self._graph:
            self._setup_workflow()
        
        async for output in self._graph.astream(state):
            if output:
                return output
        return state

    async def process_section(self, section_number: int) -> Dict[str, Any]:
        """Process a complete section through the workflow.
        
        Args:
            section_number: Section number to process
            
        Returns:
            Dict[str, Any]: Processed game state
        """
        try:
            # Create initial state
            state = await self.state_manager.create_initial_state()
            state["section_number"] = section_number
            
            # Process through workflow
            return await self._process_workflow(state)
            
        except Exception as e:
            logger.error(f"Error processing section {section_number}: {str(e)}")
            return self.state_manager.create_error_state(str(e))

    async def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input and update game state accordingly.
        
        Args:
            user_input: User's response or decision
            
        Returns:
            Dict[str, Any]: Updated game state
        """
        try:
            # Get current state and update with user input
            current_state = await self.trace_manager.get_state()
            updated_state = await self.state_manager.handle_decision(user_input, current_state)
            
            # Process through workflow
            return await self._process_workflow(updated_state)
            
        except Exception as e:
            logger.error(f"Error processing user input: {str(e)}")
            return self.state_manager.create_error_state(str(e))

    async def initialize(self) -> None:
        """Initialize the story graph and its initial state."""
        logger.debug("Initializing story graph")
        try:
            initial_state = {}
            await self._initialize_state(initial_state)
            logger.info("Story graph initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize story graph: {e}")
            raise
