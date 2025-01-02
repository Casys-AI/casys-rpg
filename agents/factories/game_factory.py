"""
Game Factory Module
Creates and configures game components.
"""

import logging
from typing import Optional, Dict, Union, TYPE_CHECKING

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

from managers.protocols.workflow_manager_protocol import WorkflowManagerProtocol
from managers.protocols.state_manager_protocol import StateManagerProtocol
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
from managers.protocols.character_manager_protocol import CharacterManagerProtocol
from managers.protocols.trace_manager_protocol import TraceManagerProtocol
from managers.protocols.rules_manager_protocol import RulesManagerProtocol
from managers.protocols.decision_manager_protocol import DecisionManagerProtocol
from managers.protocols.narrator_manager_protocol import NarratorManagerProtocol

from agents.protocols.narrator_agent_protocol import NarratorAgentProtocol
from agents.protocols.rules_agent_protocol import RulesAgentProtocol
from agents.protocols.decision_agent_protocol import DecisionAgentProtocol
from agents.protocols.trace_agent_protocol import TraceAgentProtocol
from agents.protocols.story_graph_protocol import StoryGraphProtocol

from models.types.agent_types import GameAgents
from models.types.manager_types import GameManagers

logger = logging.getLogger(__name__)

# Type alias for manager protocols
ManagerProtocols = Union[
    WorkflowManagerProtocol,
    StateManagerProtocol,
    CacheManagerProtocol,
    CharacterManagerProtocol,
    TraceManagerProtocol,
    RulesManagerProtocol,
    DecisionManagerProtocol,
    NarratorManagerProtocol
]

# Type alias for agent protocols
AgentProtocols = Union[
    NarratorAgentProtocol,
    RulesAgentProtocol,
    DecisionAgentProtocol,
    TraceAgentProtocol
]

class GameFactory:
    """Factory for creating game components."""
    
    def __init__(self, config: Optional[GameConfig] = None):
        """Initialize GameFactory.
        
        Args:
            config: Configuration for game components
        """
        self._config = config or GameConfig.create_default()
        self._cache_manager = CacheManager(self._config.manager_configs.storage_config)
        
    def _create_managers(self) -> Dict[str, ManagerProtocols]:
        """Create all game managers.
        
        Returns:
            Dict[str, ManagerProtocols]: Container with all managers
        """
        try:
            logger.debug("Creating managers")
            manager_configs = self._config.manager_configs
            
            # Create managers with their specific configs
            # 1. D'abord character_manager car state_manager en dépend
            character_manager = CharacterManager(
                manager_configs.character_config or manager_configs.storage_config, 
                self._cache_manager
            )
            
            # 2. Ensuite state_manager avec character_manager
            state_manager = StateManager(
                manager_configs.storage_config, 
                self._cache_manager,
                character_manager
            )
            
            # 3. Les autres managers
            trace_manager = TraceManager(
                manager_configs.trace_config or manager_configs.storage_config, 
                self._cache_manager
            )
            rules_manager = RulesManager(
                manager_configs.rules_config or manager_configs.storage_config, 
                self._cache_manager
            )
            decision_manager = DecisionManager()  # No config needed for now
            narrator_manager = NarratorManager(manager_configs.storage_config, self._cache_manager)
            workflow_manager = self._create_workflow_manager(state_manager, rules_manager)
            
            managers = {
                "state_manager": state_manager,
                "cache_manager": self._cache_manager,
                "character_manager": character_manager,
                "trace_manager": trace_manager,
                "rules_manager": rules_manager,
                "decision_manager": decision_manager,
                "narrator_manager": narrator_manager,
                "workflow_manager": workflow_manager
            }
            
            return managers
            
        except Exception as e:
            logger.error(f"Failed to create managers: {str(e)}")
            raise
        
    def _create_workflow_manager(
        self,
        state_manager: StateManagerProtocol,
        rules_manager: RulesManagerProtocol
    ) -> WorkflowManagerProtocol:
        """Create workflow manager instance.
        
        Args:
            state_manager: State manager instance
            rules_manager: Rules manager instance
            
        Returns:
            WorkflowManagerProtocol: Workflow manager instance
        """
        from managers.workflow_manager import WorkflowManager
        return WorkflowManager(state_manager, rules_manager)

    def _create_agents(self, managers: Dict[str, ManagerProtocols]) -> Dict[str, AgentProtocols]:
        """Create all game agents.
        
        Args:
            managers: Container with all managers
            
        Returns:
            Dict[str, AgentProtocols]: Container with all agents
        """
        try:
            logger.debug("Creating agents")
            agent_configs = self._config.agent_configs
            
            # Import agents here to avoid circular imports
            from agents.narrator_agent import NarratorAgent
            from agents.rules_agent import RulesAgent
            from agents.decision_agent import DecisionAgent
            from agents.trace_agent import TraceAgent
            
            # Create agents
            agents = {
                "narrator_agent": NarratorAgent(
                    config=agent_configs.narrator_config,
                    narrator_manager=managers["narrator_manager"]
                ),
                "rules_agent": RulesAgent(
                    config=agent_configs.rules_config,
                    rules_manager=managers["rules_manager"]
                ),
                "decision_agent": DecisionAgent(
                    config=agent_configs.decision_config,
                    decision_manager=managers["decision_manager"]
                ),
                "trace_agent": TraceAgent(
                    config=agent_configs.trace_config,
                    trace_manager=managers["trace_manager"]
                )
            }
            
            return agents
            
        except Exception as e:
            logger.error(f"Failed to create agents: {str(e)}")
            raise
            
    def _validate_managers(self, managers: Dict[str, ManagerProtocols]) -> None:
        """Validate that all required managers are present and properly initialized."""
        required_managers = [
            ("state_manager", managers["state_manager"]),
            ("cache_manager", managers["cache_manager"]),
            ("character_manager", managers["character_manager"]),
            ("trace_manager", managers["trace_manager"]),
            ("decision_manager", managers["decision_manager"]),
            ("rules_manager", managers["rules_manager"]),
            ("narrator_manager", managers["narrator_manager"]),
            ("workflow_manager", managers["workflow_manager"])
        ]
        
        for name, manager in required_managers:
            if not manager:
                raise Exception(f"Required manager {name} is not initialized")
                
    def _validate_agents(self, agents: Dict[str, AgentProtocols]) -> None:
        """Validate that all required agents are present and properly initialized."""
        required_agents = [
            ("narrator_agent", agents["narrator_agent"]),
            ("rules_agent", agents["rules_agent"]),
            ("decision_agent", agents["decision_agent"]),
            ("trace_agent", agents["trace_agent"])
        ]
        
        for name, agent in required_agents:
            if not agent:
                raise Exception(f"Required agent {name} is not initialized")
                
    def create_game_components(self) -> tuple[Dict[str, AgentProtocols], Dict[str, ManagerProtocols]]:
        """Create all game components.
        
        Returns:
            tuple[Dict[str, AgentProtocols], Dict[str, ManagerProtocols]]: All game components
            
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

    def create_story_graph(self, config: AgentConfigBase, managers: Dict[str, ManagerProtocols], agents: Dict[str, AgentProtocols]) -> StoryGraphProtocol:
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
            
            from agents.story_graph import StoryGraph
            
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
