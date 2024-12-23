"""Game factory module for creating game components."""
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass
from langchain_openai import ChatOpenAI

from config.game_config import GameConfig
from agents.base_agent import BaseAgent
from agents.protocols.story_graph_protocol import StoryGraphProtocol
from agents.protocols.narrator_agent_protocol import NarratorAgentProtocol
from agents.protocols.rules_agent_protocol import RulesAgentProtocol
from agents.protocols.decision_agent_protocol import DecisionAgentProtocol
from agents.protocols.trace_agent_protocol import TraceAgentProtocol

from managers.state_manager import StateManager
from managers.cache_manager import CacheManager
from managers.character_manager import CharacterManager
from managers.trace_manager import TraceManager
from managers.rules_manager import RulesManager
from managers.decision_manager import DecisionManager
from managers.narrator_manager import NarratorManager

from managers.protocols.narrator_manager_protocol import NarratorManagerProtocol
from managers.protocols.state_manager_protocol import StateManagerProtocol
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
from managers.protocols.character_manager_protocol import CharacterManagerProtocol
from managers.protocols.trace_manager_protocol import TraceManagerProtocol
from managers.protocols.rules_manager_protocol import RulesManagerProtocol
from managers.protocols.decision_manager_protocol import DecisionManagerProtocol


@dataclass
class GameManagers:
    """Container for all game managers."""
    state_manager: StateManagerProtocol
    cache_manager: CacheManagerProtocol
    character_manager: CharacterManagerProtocol
    trace_manager: TraceManagerProtocol
    rules_manager: RulesManagerProtocol
    decision_manager: DecisionManagerProtocol
    narrator_manager: NarratorManagerProtocol

@dataclass
class GameAgents:
    """Container for all game agents."""
    narrator_agent: NarratorAgentProtocol
    rules_agent: RulesAgentProtocol
    decision_agent: DecisionAgentProtocol
    trace_agent: TraceAgentProtocol
    story_graph: Optional[StoryGraphProtocol] = None

class GameFactory:
    """Factory for creating game components."""

    def __init__(self, config: Optional[GameConfig] = None):
        """Initialize GameFactory with configuration."""
        self._config = config or GameConfig.create_default()
        self._cache_manager = CacheManager(self._config.manager_configs.storage_config)
        self._llm = self._create_llm()

    def create_game_components(self) -> tuple[GameAgents, GameManagers]:
        """Create all game components.
        
        Returns:
            tuple[GameAgents, GameManagers]: All game components
        """
        managers = self._create_managers()
        agents = self._create_agents(managers)
        story_graph = self.create_story_graph(agents, managers)
        agents.story_graph = story_graph
        return agents, managers

    def _create_managers(self) -> GameManagers:
        """Create all game managers."""
        manager_configs = self._config.manager_configs
        
        return GameManagers(
            state_manager=StateManager(
                manager_configs.storage_config, 
                self._cache_manager
            ),
            cache_manager=self._cache_manager,
            character_manager=CharacterManager(
                manager_configs.character_config or manager_configs.storage_config, 
                self._cache_manager
            ),
            trace_manager=TraceManager(
                manager_configs.trace_config or manager_configs.storage_config, 
                self._cache_manager
            ),
            rules_manager=RulesManager(
                manager_configs.rules_config or manager_configs.storage_config, 
                self._cache_manager
            ),
            decision_manager=DecisionManager(),
            narrator_manager=NarratorManager(
                manager_configs.storage_config, 
                self._cache_manager
            )
        )

    def _create_agents(self, managers: GameManagers) -> GameAgents:
        """Create all agent instances.
        
        Args:
            managers: Container with all manager instances
            
        Returns:
            GameAgents: Container with all created agents
        """
        from agents.narrator_agent import NarratorAgent
        from agents.rules_agent import RulesAgent
        from agents.decision_agent import DecisionAgent
        from agents.trace_agent import TraceAgent
        
        agent_configs = self._config.agent_configs
        
        return GameAgents(
            narrator_agent=NarratorAgent.create('narrator', 
                agent_configs.narrator_config, 
                narrator_manager=managers.narrator_manager),
            rules_agent=RulesAgent.create('rules', 
                agent_configs.rules_config, 
                rules_manager=managers.rules_manager),
            decision_agent=DecisionAgent.create('decision', 
                agent_configs.decision_config, 
                decision_manager=managers.decision_manager),
            trace_agent=TraceAgent.create('trace', 
                agent_configs.trace_config, 
                trace_manager=managers.trace_manager)
        )

    def create_story_graph(self, agents: GameAgents, managers: GameManagers) -> StoryGraphProtocol:
        """Create the story graph component.
        
        Args:
            agents: Container with all game agents
            managers: Container with all game managers
            
        Returns:
            Initialized story graph
        """
        from agents.story_graph import StoryGraph
        
        return StoryGraph(
            config=self._config.agent_configs.story_graph_config,
            narrator_agent=agents.narrator_agent,
            rules_agent=agents.rules_agent,
            decision_agent=agents.decision_agent,
            trace_agent=agents.trace_agent,
            state_manager=managers.state_manager
        )

    def _create_llm(self) -> ChatOpenAI:
        """Create LLM instance."""
        return ChatOpenAI(
            model=self._config.model_type.value,
            temperature=self._config.temperature
        )
