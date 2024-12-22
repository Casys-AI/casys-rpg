"""Protocols package for agent interfaces."""

from agents.protocols.base_agent_protocol import BaseAgentProtocol
from agents.protocols.rules_agent_protocol import RulesAgentProtocol
from agents.protocols.narrator_agent_protocol import NarratorAgentProtocol
from agents.protocols.decision_agent_protocol import DecisionAgentProtocol
from agents.protocols.trace_agent_protocol import TraceAgentProtocol
from agents.protocols.story_graph_protocol import StoryGraphProtocol

__all__ = [
    'BaseAgentProtocol',
    'RulesAgentProtocol',
    'NarratorAgentProtocol',
    'DecisionAgentProtocol',
    'TraceAgentProtocol',
    'StoryGraphProtocol'
]
