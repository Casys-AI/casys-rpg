# config/managers/agent_manager_config.py
"""Agent Manager configuration."""
from dataclasses import dataclass
from agents.narrator_agent import NarratorAgent
from agents.rules_agent import RulesAgent
from agents.decision_agent import DecisionAgent
from agents.trace_agent import TraceAgent
from managers.state_manager import StateManager
from managers.cache_manager import CacheManager
from managers.character_manager import CharacterManager
from managers.trace_manager import TraceManager

@dataclass
class AgentManagerConfig:
    """Configuration for AgentManager."""
    narrator_agent: NarratorAgent
    rules_agent: RulesAgent
    decision_agent: DecisionAgent
    trace_agent: TraceAgent
    state_manager: StateManager
    cache_manager: CacheManager
    character_manager: CharacterManager
    trace_manager: TraceManager
