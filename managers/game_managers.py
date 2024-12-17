"""
Game Managers Module
This module contains the core managers responsible for game state, agent coordination,
and event handling following the Casys RPG architecture.
"""

from typing import Dict, Optional, Any, List, AsyncGenerator
from pydantic import BaseModel
from event_bus import EventBus, Event
import logging
import os
from agents.models import GameState
import asyncio

logger = logging.getLogger(__name__)

class StateManager:
    """
    Responsible for managing the game state and its transitions.
    
    Attributes:
        event_bus (EventBus): Event bus for state updates
        
    Methods:
        initialize_state(): Creates initial game state
        update_section_state(section_number, content): Updates state with new section
        update_game_stats(stats): Updates game statistics
    """
    
    def __init__(self, event_bus: EventBus):
        """Initialize StateManager with event bus."""
        self.event_bus = event_bus
        self._state = None

    async def initialize(self):
        """Initialize the state manager and create initial state."""
        self._state = await self.initialize_state()
        return self._state

    async def initialize_state(self) -> Dict:
        """
        Initialize a new game state with default values and Pydantic validation.
        
        Returns:
            Dict: Validated initial game state
        """
        try:
            initial_state = GameState(
                section_number=1,
                formatted_content="Bienvenue dans Casys RPG !",
                current_section={
                    "number": 1,
                    "content": "Bienvenue dans Casys RPG !",
                    "choices": [],
                    "stats": {}
                },
                rules={
                    "needs_dice": False,
                    "dice_type": "normal",
                    "conditions": [],
                    "next_sections": [],
                    "rules_summary": ""
                },
                decision={
                    "awaiting_action": "user_input",
                    "section_number": 1
                },
                stats={},
                history=[],
                error=None,
                needs_content=True,
                user_response=None,
                dice_result=None,
                trace={
                    "stats": {
                        "Caractéristiques": {
                            "Habileté": 10,
                            "Chance": 5,
                            "Endurance": 8
                        },
                        "Ressources": {
                            "Or": 100,
                            "Gemme": 5
                        },
                        "Inventaire": {
                            "Objets": ["Épée", "Bouclier"]
                        }
                    },
                    "history": []
                },
                debug=False
            )
            validated_state = initial_state.model_dump()
            self._state = validated_state
            await self.event_bus.update_state(validated_state)
            return validated_state
        except Exception as e:
            logger.error(f"Error initializing state: {str(e)}")
            return {"error": str(e)}

    async def initialize_trace(self, state: Dict) -> Dict:
        """
        Initialize trace if not present.
        
        Args:
            state: Current game state
            
        Returns:
            Dict: Updated state with initialized trace
        """
        if not state.get("trace"):
            # S'assurer que nous avons tous les champs requis
            default_state = {
                "section_number": state.get("section_number", 1),
                "current_section": state.get("current_section", {
                    "number": 1,
                    "content": None,
                    "choices": [],
                    "stats": {}
                }),
                "formatted_content": state.get("formatted_content"),
                "rules": state.get("rules", {
                    "needs_dice": False,
                    "dice_type": "normal",
                    "conditions": [],
                    "next_sections": [],
                    "rules_summary": ""
                }),
                "decision": state.get("decision", {
                    "awaiting_action": "user_input",
                    "section_number": 1
                }),
                "error": state.get("error"),
                "needs_content": state.get("needs_content", True),
                "trace": {
                    "stats": {
                        "Caractéristiques": {
                            "Habileté": 10,
                            "Chance": 5,
                            "Endurance": 8
                        },
                        "Ressources": {
                            "Or": 100,
                            "Gemme": 5
                        },
                        "Inventaire": {
                            "Objets": ["Épée", "Bouclier"]
                        }
                    },
                    "history": []
                }
            }
            
            # Mettre à jour l'état avec les valeurs par défaut
            state.update(default_state)
            
            try:
                # Validate with Pydantic
                validated_state = GameState(**state)
                state = validated_state.model_dump()
                await self.event_bus.update_state(state)
            except Exception as e:
                logger.error(f"Error initializing trace: {str(e)}")
                state["error"] = str(e)
        return state

    async def update_section_state(self, section_number: int, content: Optional[str] = None) -> None:
        """
        Update section state with Pydantic validation.
        
        Args:
            section_number: New section number
            content: Optional section content
        """
        try:
            state = await self.event_bus.get_state()
            
            # Preserve existing state
            new_state = state.copy() if isinstance(state, dict) else {}
            
            # Update fields
            new_state["section_number"] = section_number
            if content is not None:
                new_state["content"] = content
                new_state["formatted_content"] = content  # Also update formatted content
                new_state["needs_content"] = False
            
            # Validate with Pydantic
            validated_state = GameState(**new_state)
            await self.event_bus.update_state(validated_state.model_dump())
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
            state = await self.event_bus.get_state()
            if "trace" not in state:
                state["trace"] = self._get_default_trace()
            state["trace"]["stats"].update(stats)
            
            # Validate with Pydantic
            validated_state = GameState(**state)
            await self.event_bus.update_state(validated_state.model_dump())
        except Exception as e:
            logger.error(f"Error updating game stats: {str(e)}")
            raise
            
    def _get_default_trace(self) -> Dict:
        """
        Get default trace data.
        
        Returns:
            Dict: Default trace structure
        """
        return {
            "stats": {
                "Caractéristiques": {
                    "Habileté": 10,
                    "Chance": 5,
                    "Endurance": 8
                },
                "Ressources": {
                    "Or": 100,
                    "Gemme": 5
                },
                "Inventaire": {
                    "Objets": ["Épée", "Bouclier"]
                }
            },
            "history": []
        }

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
        self.state_manager = state_manager

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

    async def process_section(self, section_number: int, content: str) -> Dict:
        """
        Process a complete section through all agents.
        
        Args:
            section_number: Section number to process
            content: Section content
            
        Returns:
            Dict: Updated game state
        """
        # Update section state first
        await self.state_manager.update_section_state(section_number, content)
        
        # Get updated state
        state = await self.event_bus.get_state()
        
        # Run narrator and rules agents in parallel
        narrator_task = asyncio.create_task(self.process_narrator(state))
        rules_task = asyncio.create_task(self.process_rules(state))
        
        # Wait for both to complete
        narrator_result, rules_result = await asyncio.gather(narrator_task, rules_task)
        
        # Merge results
        state.update(narrator_result)
        state.update(rules_result)
        
        # Process decision with combined state
        state = await self.process_decision(state)
        
        return state
        
    async def process_narrator(self, state: Dict) -> Dict:
        """Process state through narrator agent"""
        try:
            result = await self.narrator.ainvoke(state)
            processed_state = state.copy()
            
            async for narrator_state in result:
                await self.event_bus.emit_agent_result("narrator_updated", narrator_state)
                processed_state.update(narrator_state)
            return processed_state
        except Exception as e:
            logger.error(f"Error in NarratorAgent: {str(e)}", exc_info=True)
            return {"error": str(e)}
            
    async def process_rules(self, state: Dict) -> Dict:
        """Process state through rules agent"""
        try:
            result = await self.rules.ainvoke(state)
            processed_state = state.copy()
            
            async for rules in result:
                await self.event_bus.emit_agent_result("rules_updated", rules)
                processed_state.update(rules)
            return processed_state
        except Exception as e:
            logger.error(f"Error in RulesAgent: {str(e)}", exc_info=True)
            return {"error": str(e)}
            
    async def process_decision(self, state: Dict) -> Dict:
        """Process state through decision agent"""
        try:
            rules = state.get("rules", {})
            if not rules:
                return state.copy()
            
            decision_input = {"rules": rules.copy()}
            result = await self.decision.ainvoke(decision_input)
            
            async for decision_result in result:
                if decision_result and "decision" in decision_result:
                    if decision_result["decision"].get("awaiting_action") is None:
                        decision_result["decision"]["awaiting_action"] = "choice"
                    await self.event_bus.emit_agent_result("decision_updated", decision_result)
                    return decision_result
            return state.copy()
        except Exception as e:
            logger.error(f"Error in DecisionAgent: {str(e)}", exc_info=True)
            return {"error": str(e)}

    async def handle_user_choice(self, choice: str):
        """Handle user choice"""
        try:
            state = await self.event_bus.get_state()
            if not state:
                state = {'section_number': 1}
            state["user_response"] = choice
            await self.event_bus.update_state(state)
            return state
        except Exception as e:
            logger.error(f"Error handling user choice: {str(e)}")
            return {"error": f"Error handling user choice: {str(e)}"}

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
