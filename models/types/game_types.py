"""
Game type definitions.
"""

from dataclasses import dataclass
from typing import Optional

from agents.protocols.narrator_agent_protocol import NarratorAgentProtocol
from agents.protocols.rules_agent_protocol import RulesAgentProtocol
from agents.protocols.decision_agent_protocol import DecisionAgentProtocol
from agents.protocols.trace_agent_protocol import TraceAgentProtocol

from managers.protocols.state_manager_protocol import StateManagerProtocol
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
from managers.protocols.character_manager_protocol import CharacterManagerProtocol
from managers.protocols.trace_manager_protocol import TraceManagerProtocol
from managers.protocols.rules_manager_protocol import RulesManagerProtocol
from managers.protocols.decision_manager_protocol import DecisionManagerProtocol
from managers.protocols.narrator_manager_protocol import NarratorManagerProtocol
from managers.protocols.workflow_manager_protocol import WorkflowManagerProtocol

@dataclass
class GameManagers:
    """Container for all game managers."""
    state_manager: StateManagerProtocol
    cache_manager: CacheManagerProtocol
    character_manager: CharacterManagerProtocol
    trace_manager: TraceManagerProtocol
    rules_manager: RulesManagerProtocol
    decision_manager: DecisionManagerProtocol
    narrator_manager: NarratorManagerProtocol
    workflow_manager: WorkflowManagerProtocol

@dataclass
class GameAgents:
    """Container for all game agents."""
    narrator_agent: Optional[NarratorAgentProtocol] = None
    rules_agent: Optional[RulesAgentProtocol] = None
    decision_agent: Optional[DecisionAgentProtocol] = None
    trace_agent: Optional[TraceAgentProtocol] = None
