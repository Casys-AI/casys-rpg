"""
Rules Agent Protocol Module
Defines the interface for the Rules Agent
"""

from typing import Dict, Optional, Protocol, runtime_checkable
from models.rules_model import RulesModel
from agents.protocols.base_agent_protocol import BaseAgentProtocol

@runtime_checkable
class RulesAgentProtocol(BaseAgentProtocol, Protocol):
    """Protocol defining the interface for the Rules Agent."""
    pass