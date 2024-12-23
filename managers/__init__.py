"""Manager package."""
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
from managers.protocols.state_manager_protocol import StateManagerProtocol
from managers.protocols.character_manager_protocol import CharacterManagerProtocol
from managers.protocols.agent_manager_protocol import AgentManagerProtocol
from managers.protocols.trace_manager_protocol import TraceManagerProtocol
from managers.protocols.rules_manager_protocol import RulesManagerProtocol
from managers.protocols.decision_manager_protocol import DecisionManagerProtocol
from managers.protocols.narrator_manager_protocol import NarratorManagerProtocol

__all__ = [
    # Protocols
    'CacheManagerProtocol',
    'StateManagerProtocol',
    'CharacterManagerProtocol',
    'AgentManagerProtocol',
    'TraceManagerProtocol',
    'RulesManagerProtocol',
    'DecisionManagerProtocol',
    'NarratorManagerProtocol',
]

def get_manager(manager_type: str):
    """Get a manager instance by type."""
    if manager_type == 'cache':
        from managers.cache_manager import CacheManager
        return CacheManager
    elif manager_type == 'state':
        from managers.state_manager import StateManager
        return StateManager
    elif manager_type == 'character':
        from managers.character_manager import CharacterManager
        return CharacterManager
    elif manager_type == 'agent':
        from managers.agent_manager import AgentManager
        return AgentManager
    elif manager_type == 'trace':
        from managers.trace_manager import TraceManager
        return TraceManager
    else:
        raise ValueError(f"Unknown manager type: {manager_type}")
