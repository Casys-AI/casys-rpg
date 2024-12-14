from typing import Dict, Callable, List, Any
from pydantic import BaseModel, Field
import asyncio
import logging
from contextlib import contextmanager
from datetime import datetime

class Event(BaseModel):
    """Représente un événement dans le système"""
    type: str = Field(..., description="Type de l'événement")
    data: Any = Field(..., description="Données de l'événement")
    timestamp: datetime = Field(default_factory=datetime.now, description="Horodatage de l'événement")
    source: str = Field(default=None, description="Source de l'événement")

    @property
    def name(self) -> str:
        return self.type

class EventBus:
    """Bus d'événements pour la communication entre agents"""
    
    def __init__(self):
        self.listeners: Dict[str, List[Callable]] = {}
        self.history: List[Event] = []
        self.logger = logging.getLogger("EventBus")

    async def subscribe(self, event_type: str, listener: Callable[[Event], None]):
        """Abonne un listener à un type d'événement"""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(listener)
        self.logger.debug(f"New subscriber for {event_type}")

    async def emit(self, event: Event):
        """Émet un événement aux listeners"""
        self.history.append(event)
        self.logger.debug(f"Event emitted: {event.type} from {event.source}")
        
        if event.type in self.listeners:
            await asyncio.gather(
                *[self._safe_execute(listener, event) for listener in self.listeners[event.type]]
            )

    async def _safe_execute(self, listener: Callable[[Event], None], event: Event):
        """Exécute un listener de manière sécurisée"""
        try:
            if asyncio.iscoroutinefunction(listener):
                await listener(event)
            else:
                listener(event)
        except Exception as e:
            self.logger.error(f"Error in listener for {event.type}: {str(e)}")

    @contextmanager
    def event_context(self, event_type: str, source: str):
        """Context manager pour tracer les événements"""
        start_time = datetime.now()
        try:
            yield
        finally:
            duration = datetime.now() - start_time
            self.logger.debug(f"Event {event_type} from {source} took {duration}")

    def get_history(self) -> List[Event]:
        """Récupère l'historique des événements"""
        return self.history.copy()

# Instance singleton
event_bus = EventBus()