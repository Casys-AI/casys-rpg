"""Game Factory module for creating game components."""
from typing import Dict, Any, Optional, Type

from config.game_config import GameConfig
from config.paths_config import PathsConfig
from config.game_constants import GameMode
from config.managers.agent_manager_config import AgentManagerConfig

from managers.state_manager import StateManager
from managers.cache_manager import CacheManager
from managers.character_manager import CharacterManager
from managers.agent_manager import AgentManager
from managers.trace_manager import TraceManager

from agents.narrator_agent import NarratorAgent
from agents.rules_agent import RulesAgent
from agents.decision_agent import DecisionAgent
from agents.trace_agent import TraceAgent
from agents.story_graph import StoryGraph

@dataclass
class AgentManagerConfig:
    narrator_agent: NarratorAgent
    rules_agent: RulesAgent
    decision_agent: DecisionAgent
    trace_agent: TraceAgent
    state_manager: StateManager
    cache_manager: CacheManager
    character_manager: CharacterManager
    trace_manager: TraceManager

class GameFactory:
    """Factory for creating and configuring game components."""
    
    def __init__(
        self,
        game_config: Optional[GameConfig] = None,
        paths_config: Optional[PathsConfig] = None
    ):
        """Initialize the game factory.
        
        Args:
            game_config: Optional game configuration
            paths_config: Optional paths configuration
        """
        self.game_config = game_config or GameConfig()
        self.paths_config = paths_config or PathsConfig()
        
    def create_managers(self) -> Dict[str, Any]:
        """Create all game managers.
        
        Returns:
            Dictionary of manager instances
        """
        managers = {
            "state": self._create_state_manager(),
            "cache": self._create_cache_manager(),
            "character": self._create_character_manager(),
            "trace": self._create_trace_manager()
        }
        
        # Initialize managers
        for manager in managers.values():
            manager.initialize()
            
        return managers
        
    def create_agents(self, managers: Dict[str, Any]) -> Dict[str, Any]:
        """Create all game agents.
        
        Args:
            managers: Dictionary of manager instances
            
        Returns:
            Dictionary of agent instances
        """
        agents = {
            "narrator": self._create_narrator_agent(managers),
            "rules": self._create_rules_agent(managers),
            "decision": self._create_decision_agent(managers),
            "trace": self._create_trace_agent(managers)
        }
        
        # Initialize story graph
        agents["story"] = self._create_story_graph(agents, managers)
        
        return agents
        
    def _create_state_manager(self) -> StateManager:
        """Create and configure state manager."""
        config = self.game_config.get_component_config("state_manager")
        return StateManager(config=config)
        
    def _create_cache_manager(self) -> CacheManager:
        """Create and configure cache manager."""
        config = self.game_config.get_component_config("cache_manager")
        return CacheManager(config=config)
        
    def _create_character_manager(self) -> CharacterManager:
        """Create and configure character manager."""
        config = self.game_config.get_component_config("character_manager")
        return CharacterManager(config=config)
        
    def _create_trace_manager(self) -> TraceManager:
        """Create and configure trace manager."""
        config = self.game_config.get_component_config("trace_manager")
        return TraceManager(config=config)
        
    def _create_narrator_agent(self, managers: Dict[str, Any]) -> NarratorAgent:
        """Create and configure narrator agent."""
        config = self.game_config.get_component_config("narrator_agent")
        return NarratorAgent(
            config=config,
            cache_manager=managers["cache"],
            state_manager=managers["state"]
        )
        
    def _create_rules_agent(self, managers: Dict[str, Any]) -> RulesAgent:
        """Create and configure rules agent."""
        config = self.game_config.get_component_config("rules_agent")
        return RulesAgent(
            config=config,
            cache_manager=managers["cache"],
            state_manager=managers["state"]
        )
        
    def _create_decision_agent(self, managers: Dict[str, Any]) -> DecisionAgent:
        """Create and configure decision agent."""
        config = self.game_config.get_component_config("decision_agent")
        return DecisionAgent(
            config=config,
            state_manager=managers["state"],
            character_manager=managers["character"]
        )
        
    def _create_trace_agent(self, managers: Dict[str, Any]) -> TraceAgent:
        """Create and configure trace agent."""
        config = self.game_config.get_component_config("trace_agent")
        return TraceAgent(
            config=config,
            cache_manager=managers["cache"]
        )
        
    def _create_story_graph(
        self,
        agents: Dict[str, Any],
        managers: Dict[str, Any]
    ) -> StoryGraph:
        """Create and configure story graph."""
        config = self.game_config.get_component_config("story_graph")
        return StoryGraph(
            config=config,
            narrator=agents["narrator"],
            rules=agents["rules"],
            decision=agents["decision"],
            trace=agents["trace"],
            state_manager=managers["state"],
            trace_manager=managers["trace"]
        )

    @property
    def agent_manager(self) -> AgentManager:
        """Create AgentManager instance with all dependencies."""
        managers = self.create_managers()
        agents = self.create_agents(managers)
        
        config = AgentManagerConfig(
            narrator_agent=agents["narrator"],
            rules_agent=agents["rules"],
            decision_agent=agents["decision"],
            trace_agent=agents["trace"],
            state_manager=managers["state"],
            cache_manager=managers["cache"],
            character_manager=managers["character"],
            trace_manager=managers["trace"]
        )
        
        manager = AgentManager(config=config)
        manager.initialize()
        return manager
