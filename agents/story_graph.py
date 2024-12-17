"""
StoryGraph Module
Manages the flow and progression of the interactive story using a state graph approach.
"""

from typing import Dict, Optional, Any, AsyncGenerator
from langgraph.graph import StateGraph
from event_bus import EventBus
from agents.narrator_agent import NarratorAgent
from agents.rules_agent import RulesAgent
from agents.decision_agent import DecisionAgent
from agents.trace_agent import TraceAgent
from agents.models import GameState
from agents.base_agent import BaseAgent
import logging
from logging_config import setup_logging
from managers.game_managers import StateManager, AgentManager
from managers.stats_manager import StatsManager
from managers.cache_manager import CacheManager

# Setup logging
setup_logging()
logger = logging.getLogger('story_graph')

class StoryGraph(BaseAgent):
    """
    Manages game flow using StateGraph for main workflow and managers for game logic.
    
    Attributes:
        event_bus (EventBus): Event bus for component communication
        state_manager (StateManager): Manages game state
        agent_manager (AgentManager): Coordinates different agents
        cache_manager (CacheManager): Handles section caching
        stats_manager (StatsManager): Manages character statistics
        graph (StateGraph): Manages game flow
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        narrator_agent: Optional[NarratorAgent] = None,
        rules_agent: Optional[RulesAgent] = None,
        decision_agent: Optional[DecisionAgent] = None,
        trace_agent: Optional[TraceAgent] = None
    ):
        """Initialize StoryGraph with agents and managers."""
        # Initialize event bus and base
        event_bus = event_bus or EventBus()
        super().__init__(event_bus)
        
        # Initialize agents
        self.narrator = narrator_agent or NarratorAgent(event_bus=self.event_bus)
        self.rules = rules_agent or RulesAgent(event_bus=self.event_bus)
        self.decision = decision_agent or DecisionAgent(event_bus=self.event_bus)
        self.trace = trace_agent or TraceAgent(event_bus=self.event_bus)
        
        # Initialize managers
        self.state_manager = StateManager(event_bus)
        self.agent_manager = AgentManager(
            self.narrator, 
            self.rules, 
            self.decision, 
            self.trace, 
            event_bus,
            self.state_manager
        )
        self.cache_manager = CacheManager()
        self.stats_manager = StatsManager(event_bus)
        
        # Setup state graph
        self.graph = self._setup_graph()

    def _setup_graph(self) -> StateGraph:
        """Setup the state graph for game flow."""
        graph = StateGraph(
            state_schema=Dict[str, Any]  # Set recursion limit during initialization
        )
        
        # Add nodes
        graph.add_node("process_section", self._process_section)
        graph.add_node("handle_decision", self._handle_decision)
        graph.add_node("update_trace", self._update_trace)
        graph.add_node("end", lambda x: x)  # Add end node
        
        # Configure flow
        graph.set_entry_point("process_section")
        graph.add_edge("process_section", "handle_decision")
        graph.add_edge("handle_decision", "update_trace")
        
        # Add conditional edges
        graph.add_conditional_edges(
            "update_trace",
            self._should_continue,
            {True: "process_section", False: "end"}
        )
        
        return graph.compile()

    async def check_section_cache(self, section_number: int) -> bool:
        """Delegate to cache manager."""
        return self.cache_manager.check_section_cache(section_number)

    async def get_character_stats(self) -> Dict:
        """Delegate to stats manager."""
        return await self.stats_manager.get_character_stats()

    async def _initialize_trace(self, state: Dict) -> Dict:
        """
        Initialize trace if not present.
        
        Args:
            state: Current game state
            
        Returns:
            Dict: Updated state with initialized trace
        """
        return await self.state_manager.initialize_trace(state)

    async def _process_section(self, state: Dict) -> Dict:
        """
        Process a section through the agent manager.
        
        Args:
            state: Current game state
            
        Returns:
            Dict: Updated game state
        """
        try:
            # Extract actual state if needed
            if isinstance(state, dict):
                if "state" in state:
                    state = state["state"]
                elif any(key in state for key in ["process_section", "handle_decision", "update_trace", "end"]):
                    for key in ["process_section", "handle_decision", "update_trace", "end"]:
                        if key in state:
                            state = state[key]
                            break

            # Initialize state if None or empty
            if not state:
                state = {
                    "section_number": 1,
                    "content": None,
                    "rules": None,
                    "decision": None,
                    "error": None,
                    "needs_content": True
                }

            # Initialize trace if needed
            state = await self._initialize_trace(state)
            if state.get("error"):
                return state

            # Verify decision for sections > 1
            section_number = state.get("section_number", 1)
            if section_number > 1 and not state.get("decision"):
                return {"error": "No decision found for section > 1"}
                    
            try:
                # Process through narrator agent first
                content_result = await self.narrator.invoke({
                    "section_number": section_number,
                    "needs_content": state.get("needs_content", True)
                })
                
                if content_result.get("error"):
                    return content_result
                    
                # Then process through rules agent
                rules_result = await self.rules.invoke({
                    "section_number": section_number,
                    "content": content_result.get("content")
                })
                
                if rules_result.get("error"):
                    return rules_result
                    
                # Merge results without duplicating state
                merged_state = {
                    **state,
                    "content": content_result.get("content"),
                    "formatted_content": content_result.get("formatted_content", ""),
                    "rules": rules_result.get("rules", {}),
                    "decision": rules_result.get("decision", {}),
                    "needs_content": False
                }
                
                return merged_state
                
            except Exception as e:
                return {"error": f"Error in agent manager while processing section {section_number}: {str(e)}"}
                
        except Exception as e:
            return {"error": f"Error processing section: {str(e)}"}

    async def _handle_decision(self, state: Dict) -> Dict:
        """
        Handle user decisions and choices.
        
        Args:
            state: Current game state
            
        Returns:
            Dict: Updated state with decision results
        """
        try:
            # Extract actual state if needed
            if isinstance(state, dict):
                if "state" in state:
                    state = state["state"]

            if state.get("user_response"):
                try:
                    # Process through decision agent
                    decision_result = await self.decision.invoke({
                        "section_number": state.get("section_number"),
                        "user_response": state.get("user_response"),
                        "rules": state.get("rules", {})
                    })
                    
                    if decision_result.get("error"):
                        return decision_result

                    # Update state with decision results
                    merged_state = {
                        **state,
                        "decision": decision_result.get("decision", {}),
                        "dice_result": None if not state.get("rules", {}).get("needs_dice") else state.get("dice_result")
                    }

                    # Handle stats updates
                    if decision_result.get("stats"):
                        await self.event_bus.emit(Event(
                            type="stats_updated",
                            data={"stats": decision_result["stats"]}
                        ))
                        merged_state["stats"] = decision_result["stats"]

                    return merged_state
                    
                except Exception as e:
                    return {"error": f"Error handling user choice: {str(e)}"}
            
            return state
            
        except Exception as e:
            return {"error": f"Error in decision handling: {str(e)}"}

    async def _update_trace(self, state: Dict) -> Dict:
        """
        Update game trace with current state.
        
        Args:
            state: Current game state
            
        Returns:
            Dict: Updated state with trace information
        """
        try:
            # Extract actual state if needed
            if isinstance(state, dict):
                if any(key in state for key in ["process_section", "handle_decision", "update_trace", "end"]):
                    for key in ["process_section", "handle_decision", "update_trace", "end"]:
                        if key in state:
                            state = state[key]
                            break

            if state.get("error"):
                return state

            try:
                # Update trace through trace agent
                result = await self.trace.invoke({"state": state})
                if result.get("error"):
                    return result
                
                return {**state, **result}
                
            except Exception as e:
                return {"error": f"Error updating trace: {str(e)}"}
                
        except Exception as e:
            return {"error": f"Error in trace update: {str(e)}"}

    def _should_continue(self, state: Dict) -> bool:
        """
        Determine if the game should continue.
        
        Args:
            state: Current game state
            
        Returns:
            bool: True if game should continue, False otherwise
        """
        # Extract actual state if needed
        if isinstance(state, dict):
            if any(key in state for key in ["process_section", "handle_decision", "update_trace", "end"]):
                for key in ["process_section", "handle_decision", "update_trace", "end"]:
                    if key in state:
                        state = state[key]
                        break
        
        # Stop if there's an error
        if state.get("error"):
            return False
            
        # Stop if we reach the end
        if state.get("end_game"):
            return False
            
        # Stop if we don't have a valid section
        if not state.get("section_number"):
            return False
            
        return True

    async def invoke(self, state: Dict) -> AsyncGenerator[Dict, None]:
        """
        Process game state through the graph.
        
        Args:
            state: Current game state
            
        Yields:
            Updated game states
        """
        try:
            if state is None:
                state = {}
                
            # Wrap state in expected structure if needed
            if not isinstance(state, dict) or "state" not in state:
                state = {"state": state}
                
            # Process section first
            processed_state = await self._process_section(state["state"])
            if "error" in processed_state:
                yield {"state": processed_state}
                return
                
            # Then handle decision if needed
            if processed_state.get("user_response"):
                processed_state = await self._handle_decision(processed_state)
                if "error" in processed_state:
                    yield {"state": processed_state}
                    return
                    
            yield {"state": processed_state}
                
        except Exception as e:
            logger.error(f"Error in StoryGraph invoke: {str(e)}")
            yield {"state": {"error": f"Error in story graph: {str(e)}"}}

    async def initialize(self):
        """Initialize the StoryGraph components."""
        try:
            # Initialize agents if needed
            if not self.narrator:
                self.narrator = self.create_narrator_agent()
            if not self.rules:
                self.rules = self.create_rules_agent()
            if not self.decision:
                self.decision = self.create_decision_agent()
            if not self.trace:
                self.trace = self.create_trace_agent()
                
            logger.info("StoryGraph initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing StoryGraph: {str(e)}")
            return False
