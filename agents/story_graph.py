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
        narrator_agent=None,
        rules_agent=None,
        decision_agent=None,
        trace_agent=None,
    ):
        """Initialise le graphe d'histoire."""
        self.event_bus = EventBus()
        
        # Les agents seront initialisés dans initialize()
        self._narrator = narrator_agent
        self._rules = rules_agent
        self._decision = decision_agent
        self._trace = trace_agent
        
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """Initialise les agents de manière asynchrone"""
        try:
            self.logger.debug("Initialisation des agents...")
            
            # Initialiser les agents si non fournis
            if not self._narrator:
                from agents.narrator_agent import NarratorAgent
                self._narrator = NarratorAgent(event_bus=self.event_bus)
                
            if not self._rules:
                from agents.rules_agent import RulesAgent
                self._rules = RulesAgent(event_bus=self.event_bus)
                
            if not self._decision:
                from agents.decision_agent import DecisionAgent
                self._decision = DecisionAgent(event_bus=self.event_bus)
                await self._decision._setup_events()  # Initialisation asynchrone
                
            if not self._trace:
                from agents.trace_agent import TraceAgent
                self._trace = TraceAgent(event_bus=self.event_bus)
            
            self.logger.debug("Agents initialisés avec succès")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation des agents: {str(e)}")
            raise

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
                
                # Extract content from narrator response
                if "state" in content_result:
                    content_result = content_result["state"]
                    
                # Then process through rules agent
                rules_result = await self.rules.invoke({
                    "section_number": section_number,
                    "content": content_result.get("content")
                })
                
                if rules_result.get("error"):
                    return rules_result
                    
                # Extract rules from rules response
                if "state" in rules_result:
                    rules_result = rules_result["state"]
                    
                # Merge results without duplicating state
                merged_state = {
                    **state,
                    "content": content_result.get("content"),
                    "formatted_content": content_result.get("formatted_content"),
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

    async def invoke(self, state: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Invoque le graphe d'histoire avec un état donné."""
        try:
            # Traiter la section avec le NarratorAgent
            content = await self._narrator.process_section(state["section_number"])
            
            # Analyser les règles avec le RulesAgent
            rules = await self._rules.analyze_rules(state["section_number"])
            
            # Traiter la décision avec le DecisionAgent
            decision = await self._decision.process_decision(
                state["user_response"] if "user_response" in state else None,
                rules
            )
            
            # Tracer l'état avec le TraceAgent
            trace = await self._trace.record_state(state)
            
            # Construire le nouvel état
            new_state = {
                "section_number": state["section_number"],
                "content": content,
                "rules": rules,
                "decision": decision,
                "trace": trace
            }
            
            yield {"state": new_state}
            
        except Exception as e:
            self.logger.error(f"Erreur dans invoke: {str(e)}")
            yield {"error": str(e)}
