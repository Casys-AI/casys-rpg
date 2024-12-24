"""
Trace Manager Module
Manages game trace persistence and history.
"""

# Standard library imports
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List
import json
import logging
import uuid

# Local imports
from config.storage_config import StorageConfig
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
from managers.protocols.trace_manager_protocol import TraceManagerProtocol
from models.errors_model import TraceError
from models.game_state import GameState
from models.trace_model import TraceModel, TraceAction, ActionType

class TraceManager(TraceManagerProtocol):
    """Manages game traces and history."""
    
    def __init__(self, config: StorageConfig, cache_manager: CacheManagerProtocol):
        """Initialize TraceManager with configuration."""
        self.config = config
        self.cache = cache_manager
        self.logger = logging.getLogger(__name__)
        self._current_trace = None
        self._current_game_id = None

    async def start_session(self) -> None:
        """Start a new game session."""
        session_id = str(datetime.now().timestamp())
        self._current_game_id = str(uuid.uuid4())
        
        self._current_trace = TraceModel(
            game_id=self._current_game_id,
            session_id=session_id,
            start_time=datetime.now(),
            history=[]
        )
        
        # Save only the current trace, not in history yet
        await self.cache.save_cached_data(
            key=self._current_trace.session_id,
            namespace="trace",
            data=self._current_trace.model_dump()
        )
        
        self.logger.info(f"Started new session {session_id} for game {self._current_game_id}")

    async def process_trace(self, state: GameState, action: Dict[str, Any]) -> None:
        """Process and store a game trace."""
        if not self._current_trace:
            await self.start_session()
            
        # Créer une copie des détails sans le type d'action
        details = action.copy()
        action_type = ActionType(details.pop("type", ActionType.ERROR))
            
        trace_action = TraceAction(
            timestamp=datetime.now(),
            section=state.section_number,
            action_type=action_type,
            details=details
        )
        
        # Créer une nouvelle trace avec l'action ajoutée
        new_history = list(self._current_trace.history)
        new_history.append(trace_action)
        self._current_trace = TraceModel(
            game_id=self._current_trace.game_id,
            session_id=self._current_trace.session_id,
            section_number=state.section_number,  
            start_time=self._current_trace.start_time,
            history=new_history,
            current_section=self._current_trace.current_section,
            current_rules=self._current_trace.current_rules,
            character=self._current_trace.character,
            error=self._current_trace.error
        )
        
        await self.save_trace()

    async def save_trace(self) -> None:
        """Save current trace to storage."""
        if not self._current_trace:
            return
            
        try:
            # Save current trace
            await self.cache.save_cached_data(
                key=self._current_trace.session_id,
                namespace="trace",
                data=self._current_trace.model_dump()
            )
            
            # Only save to history if we have actions
            if self._current_trace.history:
                await self.cache.save_cached_data(
                    key=f"history/{self._current_trace.session_id}",
                    namespace="trace",
                    data=self._current_trace.model_dump()
                )
        except Exception as e:
            self.logger.error(f"Error saving trace: {e}")
            raise TraceError(f"Failed to save trace: {e}")

    async def get_current_trace(self) -> Optional[TraceModel]:
        """Get current trace if exists."""
        return self._current_trace

    async def get_trace_history(self) -> List[TraceModel]:
        """Get all traces from storage."""
        try:
            # Récupérer toutes les traces de l'historique
            traces = await self.cache.get_cached_data(
                key="history/*",
                namespace="traces",
                model_type=TraceModel
            )
            
            if not traces:
                return []
                
            return [trace for trace in traces if isinstance(trace, TraceModel)]
        except Exception as e:
            self.logger.error(f"Error loading traces: {e}")
            raise TraceError(f"Failed to load traces: {e}")

    def get_state_feedback(self, state: GameState) -> str:
        """Get feedback about the current game state."""
        try:
            if not state or not state.trace:
                return "No state information available"
                
            last_action = state.trace.get_last_action()
            if not last_action:
                return "No actions recorded yet"
                
            # Format feedback based on action type
            action_type = last_action.get("action_type", "unknown")
            details = last_action.get("details", {})
            
            if action_type == "dice_roll":
                return f"Dice roll result: {details.get('result')} ({details.get('dice_type', 'unknown')})"
            elif action_type == "user_input":
                return f"Player response recorded: {details.get('response', 'No response')}"
            elif action_type == "decision":
                return f"Decision made: Moving to section {details.get('next_section', 'unknown')}"
            
            return "Game state processed successfully"
            
        except Exception as e:
            self.logger.error(f"Error getting state feedback: {e}")
            return f"Error getting feedback: {str(e)}"
