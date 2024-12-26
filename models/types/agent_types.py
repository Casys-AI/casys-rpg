"""Agent type definitions."""
from dataclasses import dataclass
from typing import Optional

from agents.protocols.narrator_agent_protocol import NarratorAgentProtocol
from agents.protocols.rules_agent_protocol import RulesAgentProtocol
from agents.protocols.decision_agent_protocol import DecisionAgentProtocol
from agents.protocols.trace_agent_protocol import TraceAgentProtocol

@dataclass
class GameAgents:
    """Container for all game agents."""
    narrator_agent: Optional[NarratorAgentProtocol] = None
    rules_agent: Optional[RulesAgentProtocol] = None
    decision_agent: Optional[DecisionAgentProtocol] = None
    trace_agent: Optional[TraceAgentProtocol] = None
