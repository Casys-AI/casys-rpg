"""
Trace Agent Module
Handles game state tracking and analysis.
"""

from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import logging
from pathlib import Path
from models.game_state import GameState
from models.trace_model import TraceModel
from models.character_model import CharacterModel
from config.core_config import ComponentConfig
from agents.base_agent import BaseAgent
from managers.cache_manager import CacheManager
from agents.protocols import TraceAgentProtocol

class TraceAgentConfig(ComponentConfig):
    """Configuration for TraceAgent"""
    trace_manager: Optional[Any] = None
    character_manager: Optional[Any] = None
    cache_manager: Optional[Any] = None
    dependencies: Dict[str, Any] = {}

class TraceAgent(BaseAgent, TraceAgentProtocol):
    """
    Handles game state tracking and analysis.
    This agent is responsible for:
    1. Analyzing game state changes
    2. Making decisions about state transitions
    3. Creating and analyzing game actions
    4. Providing feedback on game progression
    """
    
    def __init__(self, config: TraceAgentConfig, cache_manager: CacheManager):
        super().__init__(config=config, cache_manager=cache_manager)
        self.logger = logging.getLogger(__name__)
        
        # Get managers from dependencies
        self.trace_manager = self.config.dependencies.get("trace_manager")
        self.character_manager = self.config.dependencies.get("character_manager")

    def _create_action_from_state(self, state: GameState) -> Dict[str, Any]:
        """
        Create action entry from game state.
        Analyzes the current state to determine what action occurred.
        """
        action_type = self._determine_action_type(state)
        return {
            "timestamp": datetime.now().isoformat(),
            "section": state.section_number,
            "action_type": action_type,
            "details": self._get_action_details(state, action_type)
        }

    def _determine_action_type(self, state: GameState) -> str:
        """
        Determine the type of action from state.
        Analyzes state components to identify what kind of action occurred.
        """
        if state.dice_roll:
            return "dice_roll"
        elif state.player_input:
            return "user_input"
        elif state.decision:
            return "decision"
        return "unknown"

    def _get_action_details(self, state: GameState, action_type: str) -> Dict[str, Any]:
        """
        Get details specific to the action type.
        Extracts and formats relevant information based on the action type.
        """
        details = {}
        
        if action_type == "dice_roll" and state.dice_roll:
            details.update({
                "dice_type": state.rules.dice_type,
                "result": state.dice_roll.value,
                "dice_roll": state.dice_roll.model_dump(),
                "next_section": state.decision.section_number if state.decision else None,
                "conditions": state.rules.conditions if state.rules else []
            })
        elif action_type == "user_input" and state.player_input:
            details["response"] = state.player_input
        elif action_type == "decision" and state.decision:
            details.update({
                "next_section": state.decision.section_number,
                "conditions": state.rules.conditions if state.rules else []
            })
            
        return details

    async def analyze_state(self, state: GameState) -> GameState:
        """
        Analyze the current game state and make decisions.
        This is where the agent's intelligence comes in.
        
        Args:
            state: Current game state
            
        Returns:
            GameState: Updated game state with decisions
        """
        try:
            # Create action from current state
            action = self._create_action_from_state(state)
            
            # Process trace via manager
            if self.trace_manager:
                self.trace_manager.process_trace(state, action)
            
            # TODO: Add LLM analysis for game state
            # This will include:
            # - Analyzing player decisions and their impact
            # - Evaluating game progression
            # - Suggesting potential paths or strategies
            # - Identifying key decision points
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error analyzing game state: {e}")
            state.error = str(e)
            return state

    async def get_feedback(self, state: GameState) -> str:
        """
        Get feedback about the current game state.
        
        Args:
            state: Current game state
            
        Returns:
            str: Feedback about the current state
        """
        try:
            if self.trace_manager:
                return self.trace_manager.get_state_feedback(state)
            return "Game state processed successfully."
            
        except Exception as e:
            self.logger.error(f"Error getting feedback: {e}")
            return f"Error getting feedback: {e}"

    async def ainvoke(self, input_data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Asynchronous invocation of the agent.
        
        Args:
            input_data: Input data containing game state
            
        Yields:
            Dict[str, Any]: Updated game state
        """
        try:
            # Parse input state
            state = GameState.model_validate(input_data.get("state", input_data))
            
            # Analyze state and get decisions
            updated_state = await self.analyze_state(state)
            
            # Get feedback if needed
            if updated_state.error:
                feedback = await self.get_feedback(updated_state)
                updated_state.error = feedback
            
            yield updated_state.model_dump()
            
        except Exception as e:
            self.logger.error(f"Error in TraceAgent.ainvoke: {e}")
            yield {"error": str(e)}

    def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous version of ainvoke.
        
        Args:
            input_data: Input data containing game state
            
        Returns:
            Dict[str, Any]: Updated game state
        """
        try:
            # Parse input state
            state = GameState.model_validate(input_data.get("state", input_data))
            
            # Analyze state
            updated_state = self.analyze_state(state)
            
            return updated_state.model_dump()
            
        except Exception as e:
            self.logger.error(f"Error in TraceAgent.invoke: {e}")
            return {"error": str(e)}
