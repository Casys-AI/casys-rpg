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
from agents.story_graph import StoryGraph
from agents.protocols.story_graph_protocol import StoryGraphProtocol

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
        
    def _validate_managers(self, managers: GameManagers) -> None:
        """Validate that all required managers are present and properly initialized."""
        required_managers = [
            (managers.state_manager, "StateManager"),
            (managers.cache_manager, "CacheManager"),
            (managers.character_manager, "CharacterManager"),
            (managers.trace_manager, "TraceManager"),
            (managers.decision_manager, "DecisionManager"),
            (managers.rules_manager, "RulesManager"),
            (managers.narrator_manager, "NarratorManager"),
            (managers.workflow_manager, "WorkflowManager")
        ]
        
        for manager, name in required_managers:
            if not manager:
                raise Exception(f"Required manager {name} is not initialized")
                
    def _validate_agents(self, agents: GameAgents) -> None:
        """Validate that all required agents are present and properly initialized."""
        required_agents = [
            (agents.narrator_agent, "NarratorAgent"),
            (agents.rules_agent, "RulesAgent"),
            (agents.decision_agent, "DecisionAgent"),
            (agents.trace_agent, "TraceAgent")
        ]
        
        for agent, name in required_agents:
            if not agent:
                raise Exception(f"Required agent {name} is not initialized")
                
    def create_game_components(self) -> tuple[GameAgents, GameManagers]:
        """Create all game components.
        
        Returns:
            tuple[GameAgents, GameManagers]: All game components
            
        Raises:
            Exception: If component creation fails
        """
        try:
            managers = self._create_managers()
            self._validate_managers(managers)
            
            agents = self._create_agents(managers)
            self._validate_agents(agents)
            
            return agents, managers
            
        except Exception as e:
            logger.error("Error creating game components: {}", str(e))
            raise Exception(f"Failed to create game components: {str(e)}")

    def create_story_graph(self, config: AgentConfigBase, managers: GameManagers, agents: GameAgents) -> StoryGraphProtocol:
        """Create and configure story graph.
        
        Args:
            config: Configuration for story graph
            managers: Container with all managers
            agents: Container with all agents
            
        Returns:
            StoryGraphProtocol: Configured story graph instance
            
        Raises:
            Exception: If story graph creation fails
        """
        try:
            logger.debug("Creating story graph")
            
            # Create story graph with dependencies
            story_graph = StoryGraph(
                config=config,
                managers=managers,
                agents=agents
            )
            
            logger.debug("Story graph created successfully")
            return story_graph
            
        except Exception as e:
            logger.error("Error creating story graph: {}", str(e))
            raise Exception(f"Failed to create story graph: {str(e)}")
