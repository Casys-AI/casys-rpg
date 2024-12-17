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
        Initialize a new game state with default values and Pydantic validation.
        
        Returns:
            Dict: Validated initial game state
        """
        try:
            logger.info("Début de initialize_state")
            logger.debug("Création de l'état initial avec GameState")

            # Récupérer le contenu initial depuis le cache ou le fichier
            try:
                from managers.cache_manager import CacheManager
                cache_manager = CacheManager()
                section_content = await cache_manager.get_section_content(1)
                if not section_content:
                    section_content = "Bienvenue dans Casys RPG !"
            except Exception as e:
                logger.warning(f"Impossible de charger le contenu de la section 1: {str(e)}")
                section_content = "Bienvenue dans Casys RPG !"

            # Formater le contenu avec le NarratorAgent
            try:
                from agents.narrator_agent import NarratorAgent
                event_bus = EventBus()
                narrator = NarratorAgent(event_bus=event_bus)
                state = {
                    "section_number": 1,
                    "content": section_content,
                    "needs_content": True
                }
                narrator_response = await narrator.ainvoke(state)
                formatted_content = narrator_response["state"]["content"]
                if not formatted_content:
                    formatted_content = section_content
            except Exception as e:
                logger.warning(f"Impossible de formater le contenu: {str(e)}")
                formatted_content = section_content

            initial_state = GameState(
                section_number=1,
                current_section={
                    "number": 1,
                    "content": section_content,  
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
            logger.info("État initial créé avec succès")
            logger.debug("Validation avec model_dump")
            validated_state = initial_state.model_dump()
            logger.info("État validé avec succès")
            logger.debug(f"État validé: {validated_state}")
            self._state = validated_state
            return validated_state
        except Exception as e:
            logger.error(f"Erreur détaillée dans initialize_state: {str(e)}", exc_info=True)
            logger.error(f"Type d'erreur: {type(e)}")
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
                self._state["trace"] = self._get_default_trace()
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
            # Update section state first
            await self.state_manager.update_section_state(section_number, content)
            
            # Get updated state
            state = await self.state_manager.get_state()
            
            # Run narrator and rules agents in parallel
            narrator_task = asyncio.create_task(self.process_narrator(state))
            rules_task = asyncio.create_task(self.process_rules(state))
            
            # Wait for both to complete
            narrator_result, rules_result = await asyncio.gather(narrator_task, rules_task)
            
            # Merge results
            updated_state = {
                "state": {
                    "section_number": section_number,
                    "content": content,
                    "needs_content": False,
                    "rules": rules_result.get("state", {}).get("rules", {})
                }
            }
            
            # Process decision with combined state
            decision_result = await self.process_decision(updated_state)
            if decision_result:
                updated_state["state"].update(decision_result)
            
            return updated_state["state"]
            
        except Exception as e:
            logger.error(f"Error in process_section: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "section_number": section_number,
                "content": content
            }

    async def process_narrator(self, state: Dict) -> Dict:
        """Process state through narrator agent"""
        try:
            logger.debug(f"Input state: {state}")
            result = await self.narrator.ainvoke(state)
            print(f"Narrator raw result: {result}")
            
            if not result:
                logger.debug("No result from narrator")
                return state.copy()
                
            if not isinstance(result, dict):
                logger.debug(f"Result is not a dict: {type(result)}")
                return state.copy()
            
            # S'assurer que nous avons la structure de base
            if "state" not in result:
                logger.debug("Adding state wrapper")
                result = {"state": result}
            else:
                # Faire une copie profonde pour éviter les références partagées
                result = {"state": result["state"].copy()}
                
            print(f"Final narrator result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in NarratorAgent: {str(e)}", exc_info=True)
            return {"error": str(e)}

    async def process_rules(self, state: Dict) -> Dict:
        """Process state through rules agent"""
        try:
            result = await self.rules.ainvoke(state)
            
            if result and "state" in result and "rules" in result["state"]:
                if result["state"]["rules"].get("error"):
                    logger.warning(f"RulesAgent error: {result['state']['rules']['error']}")
                    return result
                
                return result
            
        except Exception as e:
            logger.error(f"Error in RulesAgent: {str(e)}", exc_info=True)
            return {"error": str(e)}

    async def process_decision(self, state: Dict) -> Dict:
        """Process state through decision agent"""
        try:
            # Extract only the rules part for decision agent
            rules = state.get("state", {}).get("rules", {})
            decision_input = {"state": {"rules": rules}}
            result = await self.decision.ainvoke(decision_input)
            
            if result and "decision" in result:
                if result["decision"].get("awaiting_action") is None:
                    result["decision"]["awaiting_action"] = "choice"
                return result
                
            return state.copy()
            
        except Exception as e:
            logger.error(f"Error in DecisionAgent: {str(e)}", exc_info=True)
            return {"error": str(e)}

    async def handle_user_choice(self, choice: str):
        """Handle user choice"""
        try:
            state = await self.state_manager.get_state()
            if not state:
                state = {'section_number': 1}
            state["user_response"] = choice
            await self.state_manager.update_section_state(state["section_number"], state["content"])
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
