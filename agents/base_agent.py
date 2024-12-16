"""Agent de base avec gestion d'état via EventBus."""
from typing import Dict, Optional, Any, AsyncGenerator
from event_bus import EventBus, Event
import logging

class BaseAgent:
    """Classe de base pour tous les agents."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._setup_logging()

    def _setup_logging(self):
        """Configure le logging de manière centralisée pour tous les agents."""
        self._logger = logging.getLogger(self.__class__.__name__)
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.ERROR)  # Niveau ERROR par défaut
            
    async def ainvoke(self, input_data: Dict) -> AsyncGenerator[Dict, None]:
        """Invoke async."""
        state = await self.event_bus.get_state()
        result = await self.invoke(input_data)
        yield result

    async def invoke(self, input_data: Dict, config: Optional[Dict] = None) -> Dict:
        """Invoke sync."""
        raise NotImplementedError("Subclasses must implement invoke")
