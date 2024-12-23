"""
Trace Agent Module
Handles game state tracking and analysis.
"""

from typing import Dict, Any, Optional, AsyncGenerator, Union
from datetime import datetime
import logging
from pathlib import Path
from pydantic import Field
from models.game_state import GameState
from models.trace_model import TraceModel
from models.character_model import CharacterModel
from config.agents.trace_agent_config import TraceAgentConfig
from agents.base_agent import BaseAgent
from managers.protocols.trace_manager_protocol import TraceManagerProtocol
from agents.protocols import TraceAgentProtocol
from models.errors_model import TraceError

class TraceAgent(BaseAgent):
    """Handles game state tracking and analysis."""
    
    config: TraceAgentConfig = Field(default_factory=TraceAgentConfig)
    
    def __init__(self, config: TraceAgentConfig, trace_manager: TraceManagerProtocol):
        """Initialize TraceAgent with configuration and manager."""
        super().__init__(config=config)
        self.config = config
        self.trace_manager = trace_manager
        self.logger = logging.getLogger(__name__)

    def _create_action_from_state(self, state: GameState) -> Dict[str, Any]:
        """Create action entry from game state."""
        action_type = self._determine_action_type(state)
        return {
            "timestamp": datetime.now().isoformat(),
            "section": state.section_number,
            "action_type": action_type,
            "details": self._get_action_details(state, action_type)
        }

    def _determine_action_type(self, state: GameState) -> str:
        """Determine the type of action from state."""
        if state.dice_roll:
            return "dice_roll"
        elif state.player_input:
            return "user_input"
        elif state.decision:
            return "decision"
        return "state_change"

    def _get_action_details(self, state: GameState, action_type: str) -> Dict[str, Any]:
        """Get details specific to the action type."""
        details = {
            "section_number": state.section_number,
            "timestamp": datetime.now().isoformat()
        }
        
        if action_type == "dice_roll" and state.dice_roll:
            details.update({
                "dice_type": state.rules.dice_type if state.rules else None,
                "result": state.dice_roll.value,
                "next_section": state.decision.section_number if state.decision else None
            })
        elif action_type == "user_input" and state.player_input:
            details["response"] = state.player_input
        elif action_type == "decision" and state.decision:
            details["next_section"] = state.decision.section_number
            
        if state.rules:
            details["conditions"] = state.rules.conditions
            
        return details

    async def record_state(self, state: GameState) -> TraceModel:
        """Record game state and return trace."""
        try:
            action = self._create_action_from_state(state)
            await self.trace_manager.process_trace(state, action)
            return await self.trace_manager.get_current_trace()
        except Exception as e:
            self.logger.error(f"Error recording state: {e}")
            raise TraceError(message=f"Failed to record state: {str(e)}")

    async def analyze_state(self, state: GameState) -> GameState:
        """Analyze state and add insights."""
        try:
            # Get current trace
            trace = await self.trace_manager.get_current_trace()
            
            # Add trace to state
            state.trace = trace
            
            # Add feedback
            feedback = self.trace_manager.get_state_feedback(state)
            if feedback:
                state.trace.feedback = feedback
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error analyzing state: {e}")
            return state.with_error(str(e))

    async def ainvoke(self, input_data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Process game state asynchronously."""
        try:
            # Parse input state
            state = GameState.model_validate(input_data)
            
            # Record and analyze state
            trace = await self.record_state(state)
            state.trace = trace
            updated_state = await self.analyze_state(state)
            
            yield updated_state.model_dump()
            
        except Exception as e:
            self.logger.error(f"Error in TraceAgent.ainvoke: {e}")
            yield {"error": str(e)}

# Add runtime type checking for protocol
TraceAgentProtocol.register(TraceAgent)
