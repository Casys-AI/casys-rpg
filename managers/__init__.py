"""Manager package."""
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
from managers.protocols.state_manager_protocol import StateManagerProtocol
from managers.protocols.character_manager_protocol import CharacterManagerProtocol
from managers.protocols.agent_manager_protocol import AgentManagerProtocol
from managers.protocols.trace_manager_protocol import TraceManagerProtocol

# Concrete implementations
from managers.cache_manager import CacheManager
from managers.state_manager import StateManager
from managers.character_manager import CharacterManager
from managers.agent_manager import AgentManager
from managers.trace_manager import TraceManager

__all__ = [
    # Protocols
    'CacheManagerProtocol',
    'StateManagerProtocol',
    'CharacterManagerProtocol',
    'AgentManagerProtocol',
    'TraceManagerProtocol',
    # Implementations
    'CacheManager',
    'StateManager',
    'CharacterManager',
    'AgentManager',
    'TraceManager'
]
