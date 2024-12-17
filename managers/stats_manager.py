"""
Stats Manager Module
Handles character and game statistics management.
"""

from typing import Dict
import logging
from event_bus import EventBus
from logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger('stats_manager')

class StatsManager:
    """
    Manages character and game statistics.
    
    Attributes:
        event_bus (EventBus): Event bus for component communication
    """
    
    def __init__(self, event_bus: EventBus):
        """Initialize StatsManager with event bus."""
        self.event_bus = event_bus
        
    async def get_character_stats(self) -> Dict:
        """
        Get current character statistics.
        
        Returns:
            Dict: Character statistics from trace
        """
        try:
            state = await self.event_bus.get_state()
            return state.get("trace", {}).get("stats", {})
        except Exception as e:
            logger.error(f"Error getting character stats: {str(e)}")
            return {"error": str(e)}
            
    async def update_stats(self, stats: Dict) -> None:
        """
        Update character statistics.
        
        Args:
            stats: New statistics to update
        """
        try:
            state = await self.event_bus.get_state()
            if "trace" not in state:
                state["trace"] = {}
            if "stats" not in state["trace"]:
                state["trace"]["stats"] = {}
            
            state["trace"]["stats"].update(stats)
            await self.event_bus.update_state(state)
        except Exception as e:
            logger.error(f"Error updating character stats: {str(e)}")
            raise
