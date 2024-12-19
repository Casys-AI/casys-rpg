"""
Trace Manager Module
Handles game trace persistence and history management.
"""

from typing import Dict, Optional, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import os
import json
from pathlib import Path

from config.core_config import BaseComponent
from models.game_state import GameState
from models.trace_model import TraceModel
from models.character_model import CharacterModel
from config.agent_config import TraceConfig


class TraceManager(BaseComponent[TraceConfig]):
    """Manages game trace persistence and history."""
    
    def initialize(self) -> None:
        """
        Initialize trace manager with static configuration.
        This is called once at startup.
        """
        self.logger = logging.getLogger(__name__)
        self.current_trace = None
        
        # Setup directories and file paths
        self.trace_directory = Path(self.config.trace_dir)
        self.trace_directory.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.history_file = self.trace_directory / "history.json"
        self.adventure_sheet = self.trace_directory / "adventure_sheet.json"

    async def start_session(self) -> None:
        """
        Start a new trace session.
        This loads or creates a fresh trace.
        Can be called multiple times to start new sessions.
        """
        # Initialize current state
        self.current_trace = self._load_or_create_trace()

    def _load_or_create_trace(self) -> TraceModel:
        """Load existing trace or create new one."""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    return TraceModel.model_validate(data)
            return TraceModel()
        except Exception as e:
            self.logger.error(f"Error loading trace: {e}")
            return TraceModel()

    def process_trace(self, state: GameState, action: Dict[str, Any]) -> None:
        """
        Process and record game trace from current state.
        Updates history.json with new actions and adventure_sheet.json with stats changes.
        
        Args:
            state: Current game state containing potential stat changes
            action: Action data created by TraceAgent
        """
        try:
            # Update current trace section
            self.current_trace.section_number = state.section_number
            
            # Add action to history
            self.current_trace.add_action(action)
            
            # Save updated history
            self._save_history()
            
            # Update adventure sheet if stats changed
            if state.trace and state.trace.stats:
                self._update_adventure_sheet(state.trace.stats)
                
        except Exception as e:
            self.logger.error(f"Error processing game trace: {e}")
            raise

    def _save_history(self) -> None:
        """Save current trace to history file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.current_trace.model_dump(), f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving history: {e}")
            raise

    def _update_adventure_sheet(self, stats: Dict[str, Any]) -> None:
        """Update adventure sheet with new stats."""
        try:
            current_sheet = {}
            if self.adventure_sheet.exists():
                with open(self.adventure_sheet, 'r') as f:
                    current_sheet = json.load(f)
            
            # Update sheet with new stats
            current_sheet.update(stats)
            
            # Save updated sheet
            with open(self.adventure_sheet, 'w') as f:
                json.dump(current_sheet, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error updating adventure sheet: {e}")
            raise

    def get_state_feedback(self, state: GameState) -> str:
        """
        Get feedback about current game state.
        
        Args:
            state: Current game state
            
        Returns:
            str: Feedback message
        """
        try:
            action_count = len(self.current_trace.actions)
            current_section = state.section_number
            return f"Section {current_section} - Actions taken: {action_count}"
        except Exception as e:
            self.logger.error(f"Error getting feedback: {e}")
            return "Unable to provide state feedback"

    def save_trace(self, trace: Any) -> None:
        """
        Save trace data.
        
        Args:
            trace: Trace data to save
        """
        try:
            if not self._current_session:
                self._current_session = self.create_session_dir()
            
            trace_file = self._current_session / "trace_state.json"
            with open(trace_file, "w", encoding="utf-8") as f:
                json.dump(trace.model_dump(), f, ensure_ascii=False, indent=2)
                
            self.logger.debug(f"Saved trace to {trace_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving trace: {e}")

    def load_trace(self) -> Optional[Dict[str, Any]]:
        """
        Load trace data.
        
        Returns:
            Optional[Dict[str, Any]]: Loaded trace data or None if not found
        """
        try:
            if not self._current_session:
                return None
            
            trace_file = self._current_session / "trace_state.json"
            if not trace_file.exists():
                return None
            
            with open(trace_file, "r", encoding="utf-8") as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"Error loading trace: {e}")
            return None
