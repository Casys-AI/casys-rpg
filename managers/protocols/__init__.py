"""Protocols package for manager interfaces."""

from managers.protocols.agent_manager_protocol import AgentManagerProtocol
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
from managers.protocols.character_manager_protocol import CharacterManagerProtocol
from managers.protocols.filesystemadapter_protocol import FileSystemAdapterProtocol
from managers.protocols.rules_manager_protocol import RulesManagerProtocol
from managers.protocols.state_manager_protocol import StateManagerProtocol
from managers.protocols.trace_manager_protocol import TraceManagerProtocol
from managers.protocols.decision_manager_protocol import DecisionManagerProtocol

__all__ = [
    'AgentManagerProtocol',
    'CacheManagerProtocol',
    'CharacterManagerProtocol',
    'FileSystemAdapterProtocol',
    'RulesManagerProtocol',
    'StateManagerProtocol',
    'TraceManagerProtocol',
    'DecisionManagerProtocol',
]
