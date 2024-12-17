"""
Game Managers Module
This module contains the core managers responsible for game state, agent coordination,
and event handling following the Casys RPG architecture.
"""

from typing import Dict, Optional, Any, List, AsyncGenerator
from pydantic import BaseModel
import logging
import os
from agents.models import GameState
from event_bus import EventBus, Event
import asyncio

logger = logging.getLogger(__name__)

class StateManager:
    """
    Responsible for managing the game state and its transitions.
    
    Attributes:
        _state (Dict): Current game state
        
    Methods:
        initialize_state(): Creates initial game state
        update_section_state(section_number, content): Updates state with new section
        update_game_stats(stats): Updates game statistics
    """
    
    def __init__(self):
        """Initialize StateManager."""
        self._state = None

    async def initialize(self):
        """Initialize the state manager and create initial state."""
        self._state = await self.initialize_state()
        return self._state

    async def initialize_state(self) -> Dict:
        """
        Initialize a new game state with default values from GameState model.
        
        Returns:
            Dict: Validated initial game state
        """
        try:
            logger.info("Starting initialize_state")
            
            # Create new state with default values from GameState model
            initial_state = GameState()
            
            # Get initial content from cache or use default
            try:
                from managers.cache_manager import CacheManager
                cache_manager = CacheManager()
                section_content = await cache_manager.get_section_content(1)
                if section_content:
                    initial_state.current_section.content = section_content
            except Exception as e:
                logger.warning(f"Could not load section 1 content: {str(e)}")
            
            # Format content with NarratorAgent if available
            if initial_state.current_section.content:
                try:
                    from agents.narrator_agent import NarratorAgent
                    event_bus = EventBus()
                    narrator = NarratorAgent(event_bus=event_bus)
                    narrator_response = await narrator.ainvoke(initial_state.model_dump())
                    if narrator_response and "state" in narrator_response:
                        initial_state.current_section.content = narrator_response["state"].get("content", initial_state.current_section.content)
                except Exception as e:
                    logger.warning(f"Could not format content: {str(e)}")
            
            logger.info("State initialized successfully")
            self._state = initial_state.model_dump()
            return self._state
            
        except Exception as e:
            logger.error(f"Error in initialize_state: {str(e)}", exc_info=True)
            return {"error": str(e)}

    async def initialize_trace(self, state: Dict) -> Dict:
        """
        Initialize trace if not present using GameState defaults.
        
        Args:
            state: Current game state
            
        Returns:
            Dict: Updated state with initialized trace
        """
        if not state.get("trace"):
            # Create a new GameState to get default trace
            default_state = GameState()
            state["trace"] = default_state.trace
            
        try:
            # Validate entire state
            validated_state = GameState(**state)
            return validated_state.model_dump()
        except Exception as e:
            logger.error(f"Error initializing trace: {str(e)}")
            return state

    async def update_section_state(self, section_number: int, content: Optional[str] = None) -> None:
        """
        Update section state with Pydantic validation.
        
        Args:
            section_number: New section number
            content: Optional section content
        """
        try:
            # Preserve existing state
            new_state = self._state.copy() if isinstance(self._state, dict) else {}
            
            # Update fields
            new_state["section_number"] = section_number
            if content is not None:
                new_state["content"] = content
                new_state["needs_content"] = False
            
            # Validate with Pydantic
            validated_state = GameState(**new_state)
            self._state = validated_state.model_dump()
        except Exception as e:
            logger.error(f"Error updating section state: {str(e)}")
            raise

    async def update_game_stats(self, stats: Dict) -> None:
        """
        Update game statistics with Pydantic validation.
        
        Args:
            stats: New statistics to update
        """
        try:
            if "trace" not in self._state:
                default_state = GameState()
                self._state["trace"] = default_state.trace
                
            self._state["trace"]["stats"].update(stats)
            
            # Validate with Pydantic
            validated_state = GameState(**self._state)
            self._state = validated_state.model_dump()
        except Exception as e:
            logger.error(f"Error updating game stats: {str(e)}")
            raise
            
    async def get_state(self) -> Dict:
        """
        Récupère l'état actuel du jeu.
        
        Returns:
            Dict: État actuel du jeu ou erreur
        """
        try:
            logger.info("Début de get_state dans StateManager")
            if self._state is None:
                logger.info("État non initialisé, appel de initialize_state")
                self._state = await self.initialize_state()
                logger.info("État initialisé avec succès")
            logger.debug(f"État actuel: {self._state}")
            return self._state
        except Exception as e:
            logger.error(f"Erreur détaillée dans get_state: {str(e)}", exc_info=True)
            logger.error(f"Type d'erreur: {type(e)}")
            return {"error": str(e)}

class EventManager:
    """Responsible for managing game events and notifications"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        
    async def emit_game_event(self, event_type: str, data: Dict):
        """Emit a game event"""
        try:
            await self.event_bus.emit(Event(type=event_type, data=data))
            logger.debug(f"Event emitted: {event_type} with data {self.truncate_for_log(data)}")
        except Exception as e:
            logger.error(f"Error emitting event {event_type}: {str(e)}")
            
    def truncate_for_log(self, content: Any, max_length: int = 100) -> str:
        """Truncate content for logging"""
        if not content or len(str(content)) <= max_length:
            return str(content)
        return str(content)[:max_length] + "..."
        
class AgentManager:
    """
    Coordinates different agents and manages their interactions.
    
    Attributes:
        narrator: Narrator agent instance
        rules: Rules agent instance
        decision: Decision agent instance
        trace: Trace agent instance
        event_bus (EventBus): Event bus for communication
        state_manager (StateManager): State management
    """
    
    def __init__(self, narrator=None, rules=None, decision=None, trace=None, event_bus=None, state_manager=None):
        """Initialize AgentManager with all components."""
        self.narrator = narrator
        self.rules = rules
        self.decision = decision
        self.trace = trace
        self.event_bus = event_bus
        self.state_manager = state_manager or StateManager()

    async def initialize(self, narrator=None, rules=None, decision=None, trace=None):
        """Initialize with agent instances if not provided in constructor."""
        if narrator:
            self.narrator = narrator
        if rules:
            self.rules = rules
        if decision:
            self.decision = decision
        if trace:
            self.trace = trace
            
        # Validate that required agents are present
        missing_agents = []
        if not self.narrator:
            missing_agents.append("narrator")
        if not self.rules:
            missing_agents.append("rules")
        if not self.decision:
            missing_agents.append("decision")
            
        if missing_agents:
            raise ValueError(f"Missing required agents: {', '.join(missing_agents)}")

    async def process_section(self, section_number: int, content: str) -> Dict:
        """
        Process a complete section through all agents.
        
        Args:
            section_number: Section number to process
            content: Section content
            
        Returns:
            Dict: Updated game state
        """
        try:
            # Create base state
            base_state = GameState(
                section_number=section_number,
                current_section={
                    "number": section_number,
                    "content": content,
                    "choices": [],
                    "stats": {}
                },
                needs_content=False
            )
            
            # Process with narrator and rules agents concurrently
            tasks = [
                self._process_with_agent(self.narrator, base_state.model_dump(), "narrator"),
                self._process_with_agent(self.rules, base_state.model_dump(), "rules")
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle results and combine state
            combined_state = base_state.model_dump()
            for result, agent_type in zip(results, ["narrator", "rules"]):
                if isinstance(result, Exception):
                    logger.error(f"Error in {agent_type} processing: {str(result)}")
                    combined_state["error"] = f"{agent_type} error: {str(result)}"
                elif result and "state" in result:
                    if agent_type == "narrator" and "content" in result["state"]:
                        combined_state["current_section"]["content"] = result["state"]["content"]
                    elif agent_type == "rules" and "rules" in result["state"]:
                        combined_state["rules"] = result["state"]["rules"]
            
            # Process with decision agent
            decision_result = await self._process_with_agent(
                self.decision, 
                combined_state,
                "decision"
            )
            
            if isinstance(decision_result, Exception):
                logger.error(f"Error in decision processing: {str(decision_result)}")
                combined_state["error"] = f"Decision error: {str(decision_result)}"
            elif decision_result and "state" in decision_result:
                combined_state.update(decision_result["state"])
            
            # Final validation
            try:
                final_state = GameState(**combined_state)
                return final_state.model_dump()
            except Exception as e:
                logger.error(f"Error validating final state: {str(e)}")
                return {
                    "error": f"State validation error: {str(e)}",
                    **combined_state
                }
            
        except Exception as e:
            logger.error(f"Error in process_section: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "section_number": section_number,
                "content": content
            }

    async def _process_with_agent(self, agent, state: Dict, agent_type: str) -> Dict:
        """
        Process state with a specific agent with proper error handling.
        
        Args:
            agent: Agent instance to process with
            state: Current state to process
            agent_type: Type of agent for logging
            
        Returns:
            Dict: Processed state or error
        """
        if not agent:
            raise ValueError(f"Missing {agent_type} agent")
            
        try:
            logger.debug(f"Processing with {agent_type} agent. Input state: {state}")
            result = await agent.ainvoke(state)
            logger.debug(f"{agent_type.capitalize()} result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in {agent_type} processing: {str(e)}")
            raise

    async def process_narrator(self, state: Dict) -> Dict:
        """Process state through narrator agent"""
        return await self._process_with_agent(self.narrator, state, "narrator")

    async def process_rules(self, state: Dict) -> Dict:
        """Process state through rules agent"""
        return await self._process_with_agent(self.rules, state, "rules")

    async def process_decision(self, state: Dict) -> Dict:
        """Process state through decision agent"""
        return await self._process_with_agent(self.decision, state, "decision")

    async def handle_user_choice(self, choice: str) -> Dict:
        """
        Handle user choice with proper validation.
        
        Args:
            choice: User's choice
            
        Returns:
            Dict: Updated game state
        """
        try:
            current_state = await self.state_manager.get_state()
            if not current_state:
                raise ValueError("No current game state")
                
            # Update state with user choice
            current_state["user_response"] = choice
            
            # Process with decision agent
            result = await self.process_decision(current_state)
            
            if result and "state" in result:
                # Validate and update state
                validated_state = GameState(**result["state"])
                return validated_state.model_dump()
            return current_state
            
        except Exception as e:
            logger.error(f"Error handling user choice: {str(e)}")
            return {
                "error": str(e),
                "user_response": choice
            }

class CacheManager:
    """
    Manages section caching functionality
    
    Attributes:
        cache_dir (str): Directory for cached sections
    """
    
    def __init__(self, cache_dir: str = "data/sections/cache"):
        self.cache_dir = cache_dir
        
    def check_section_cache(self, section_number: int) -> bool:
        """Check if a section is cached"""
        cache_file = os.path.join(self.cache_dir, f"{section_number}_cached.md")
        return os.path.exists(cache_file)
        
    def get_cache_path(self, section_number: int) -> str:
        """Get the cache file path for a section"""
        return os.path.join(self.cache_dir, f"{section_number}_cached.md")
