# config/managers/agent_manager_config.py
"""Agent Manager configuration."""
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.protocols.narrator_agent_protocol import NarratorAgentProtocol
    from agents.protocols.rules_agent_protocol import RulesAgentProtocol
    from agents.protocols.decision_agent_protocol import DecisionAgentProtocol
    from agents.protocols.trace_agent_protocol import TraceAgentProtocol
    from managers.protocols.state_manager_protocol import StateManagerProtocol
    from managers.protocols.cache_manager_protocol import CacheManagerProtocol
    from managers.protocols.character_manager_protocol import CharacterManagerProtocol
    from managers.protocols.trace_manager_protocol import TraceManagerProtocol
    from managers.protocols.rules_manager_protocol import RulesManagerProtocol

class AgentManagerConfig:
    """Configuration for AgentManager."""
    
    def __init__(
        self,
        narrator_agent: 'NarratorAgentProtocol',
        rules_agent: 'RulesAgentProtocol',
        decision_agent: 'DecisionAgentProtocol',
        trace_agent: 'TraceAgentProtocol',
        state_manager: 'StateManagerProtocol',
        cache_manager: 'CacheManagerProtocol',
        character_manager: 'CharacterManagerProtocol',
        trace_manager: 'TraceManagerProtocol',
        rules_manager: 'RulesManagerProtocol'
    ) -> None:
        """Initialize AgentManager configuration."""
        self.narrator_agent = narrator_agent
        self.rules_agent = rules_agent
        self.decision_agent = decision_agent
        self.trace_agent = trace_agent
        self.state_manager = state_manager
        self.cache_manager = cache_manager
        self.character_manager = character_manager
        self.trace_manager = trace_manager
        self.rules_manager = rules_manager
