"""
Trace Agent Protocol Module
Defines the interface for the Trace Agent
"""

from typing import Dict, Protocol, runtime_checkable
from models.game_state import GameState
from models.trace_model import TraceModel
from agents.protocols.base_agent_protocol import BaseAgentProtocol

@runtime_checkable
class TraceAgentProtocol(BaseAgentProtocol, Protocol):
    """Protocol defining the interface for the Trace Agent."""
    pass
