"""
Narrator Agent Protocol Module
Defines the interface for the Narrator Agent
"""

from typing import Dict, Optional, Union, Protocol, runtime_checkable
from models.narrator_model import NarratorModel
from models.errors_model import NarratorError
from agents.protocols.base_agent_protocol import BaseAgentProtocol

@runtime_checkable
class NarratorAgentProtocol(BaseAgentProtocol, Protocol):
    """Protocol defining the interface for the Narrator Agent."""
    pass
