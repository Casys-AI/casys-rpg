"""
Game Factory Module
Creates and configures game components.
"""

import logging
from typing import Optional

from config.game_config import GameConfig
from config.agents.agent_config_base import AgentConfigBase
from config.storage_config import StorageConfig

from managers.cache_manager import CacheManager
from managers.state_manager import StateManager
from managers.character_manager import CharacterManager
from managers.trace_manager import TraceManager
from managers.rules_manager import RulesManager
from managers.decision_manager import DecisionManager
from managers.narrator_manager import NarratorManager
from managers.workflow_manager import WorkflowManager

from agents.narrator_agent import NarratorAgent
from agents.rules_agent import RulesAgent
from agents.decision_agent import DecisionAgent
from agents.trace_agent import TraceAgent

from models.types.agent_types import GameAgents
from models.types.manager_types import GameManagers

logger = logging.getLogger(__name__)

class GameFactory:
    """Factory for creating game components."""
    
    def __init__(self, config: Optional[GameConfig] = None):
        """Initialize GameFactory.
        
        Args:
            config: Configuration for game components
        """
        self._config = config or GameConfig.create_default()
        self._cache_manager = CacheManager(self._config.manager_configs.storage_config)
        
    def _create_managers(self) -> GameManagers:
        """Create all game managers.
        
        Returns:
            GameManagers: Container with all managers
        """
        manager_configs = self._config.manager_configs
        
        # Create managers with their specific configs
        state_manager = StateManager(manager_configs.storage_config, self._cache_manager)
        character_manager = CharacterManager(manager_configs.character_config or manager_configs.storage_config, self._cache_manager)
        trace_manager = TraceManager(manager_configs.trace_config or manager_configs.storage_config, self._cache_manager)
        rules_manager = RulesManager(manager_configs.rules_config or manager_configs.storage_config, self._cache_manager)
        decision_manager = DecisionManager()  # No config needed for now
        narrator_manager = NarratorManager(manager_configs.storage_config, self._cache_manager)
        workflow_manager = WorkflowManager(state_manager, rules_manager)
        
        return GameManagers(
            state_manager=state_manager,
            cache_manager=self._cache_manager,
            character_manager=character_manager,
            trace_manager=trace_manager,
            rules_manager=rules_manager,
            decision_manager=decision_manager,
            narrator_manager=narrator_manager,
            workflow_manager=workflow_manager
        )
        
    def _create_agents(self, managers: GameManagers) -> GameAgents:
        """Create all game agents.
        
        Args:
            managers: Container with all managers
            
        Returns:
            GameAgents: Container with all agents
        """
        agent_configs = self._config.agent_configs
        
        # Create agents with their specific configs
        narrator_agent = NarratorAgent(agent_configs.narrator_config, managers.narrator_manager)
        rules_agent = RulesAgent(agent_configs.rules_config, managers.rules_manager)
        decision_agent = DecisionAgent(agent_configs.decision_config, managers.decision_manager)
        trace_agent = TraceAgent(agent_configs.trace_config, managers.trace_manager)
        
        return GameAgents(
            narrator_agent=narrator_agent,
            rules_agent=rules_agent,
            decision_agent=decision_agent,
            trace_agent=trace_agent
        )
        
    def create_game_components(self) -> tuple[GameAgents, GameManagers]:
        """Create all game components.
        
        Returns:
            tuple[GameAgents, GameManagers]: All game components
        """
        try:
            managers = self._create_managers()
            agents = self._create_agents(managers)
            return agents, managers
            
        except Exception as e:
            logger.error(f"Error creating game components: {e}")
            raise
