"""
Decision Agent Protocol Module
Defines the interface for the Decision Agent
"""

from typing import Dict, List, Protocol, runtime_checkable
from models.game_state import GameState
from models.decision_model import DecisionModel
from models.rules_model import RulesModel
from agents.protocols.base_agent_protocol import BaseAgentProtocol

@runtime_checkable
class DecisionAgentProtocol(BaseAgentProtocol, Protocol):
    """Protocol defining the interface for the Decision Agent."""
    pass