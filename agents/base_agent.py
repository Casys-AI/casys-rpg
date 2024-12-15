"""Agent de base avec gestion d'état via EventBus."""
from typing import Dict, Optional, Any, AsyncGenerator
from event_bus import EventBus, Event
import logging

class BaseAgent:
    """Agent de base avec gestion d'état via EventBus."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.logger = logging.getLogger(self.__class__.__name__)

    async def ainvoke(self, input_data: Dict) -> AsyncGenerator[Dict, None]:
        """Invoke async."""
        state = await self.event_bus.get_state()
        result = await self.invoke(input_data)
        yield result

    async def invoke(self, input_data: Dict, config: Optional[Dict] = None) -> Dict:
        """Invoke sync."""
        raise NotImplementedError("Subclasses must implement invoke")
