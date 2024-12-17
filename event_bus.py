"""Event bus for managing game state and events."""
from typing import Dict, Any, Callable, List, Awaitable
from dataclasses import dataclass
import asyncio
import logging
from contextlib import contextmanager
from datetime import datetime

@dataclass
class Event:
    """Event class."""
    type: str
    data: Dict[str, Any]

class EventBus:
    """
    Event bus for managing game state and events.
    
    Attributes:
        _state (Dict): Current game state
        _subscribers (Dict): Event subscribers
        _history (List): Event history
        logger (Logger): Logger instance
    """
    
    def __init__(self):
        self._state: Dict[str, Any] = {}
        self._subscribers: Dict[str, List[Callable[[Event], Awaitable[None]]]] = {}
        self._lock = asyncio.Lock()
        self.logger = logging.getLogger("EventBus")
        self._history: List[Event] = []

    async def get_state(self) -> Dict[str, Any]:
        """Get current state."""
        async with self._lock:
            return self._state.copy()

    async def update_state(self, updates: Dict[str, Any]):
        """Update state with new values."""
        async with self._lock:
            self._state.update(updates)
            await self.emit(Event(
                type="state_updated",
                data=self._state.copy()
            ))

    async def emit(self, event: Event):
        """Emit an event to all subscribers."""
        self._history.append(event)
        self.logger.debug(f"Event emitted: {event.type}")
        
        if event.type in self._subscribers:
            await asyncio.gather(
                *[self._safe_execute(callback, event) for callback in self._subscribers[event.type]]
            )
            
    async def emit_agent_result(self, event_type: str, data: Dict):
        """
        Emit an agent result event
        
        Args:
            event_type: Type of agent event
            data: Event data
        """
        try:
            await self.emit(Event(type=event_type, data=data))
            self.logger.debug(f"Agent event emitted: {event_type}")
        except Exception as e:
            self.logger.error(f"Error emitting agent event {event_type}: {str(e)}")

    async def _safe_execute(self, callback: Callable[[Event], Awaitable[None]], event: Event):
        """Execute a callback safely."""
        try:
            await callback(event)
        except Exception as e:
            self.logger.error(f"Error in callback for {event.type}: {str(e)}")

    async def subscribe(self, event_type: str, callback: Callable[[Event], Awaitable[None]]):
        """Subscribe to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        self.logger.debug(f"New subscriber for {event_type}")

    async def reset_state(self):
        """Reset state."""
        async with self._lock:
            self._state = {}
            await self.emit(Event(
                type="state_reset",
                data={}
            ))

    @contextmanager
    def event_context(self, event_type: str):
        """Context manager for tracing events."""
        start_time = datetime.now()
        try:
            yield
        finally:
            duration = datetime.now() - start_time
            self.logger.debug(f"Event {event_type} took {duration}")

    @property
    def history(self) -> List[Event]:
        """Get event history."""
        return self._history.copy()

    def get_history(self) -> List[Event]:
        """
        Récupère l'historique des événements.
        
        Returns:
            List[Event]: Liste des événements émis
        """
        return self._history.copy()

# Instance singleton
event_bus = EventBus()