"""Factory for game components initialization and configuration."""
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, model_validator
from functools import cached_property
import os

from agents.narrator_agent import NarratorAgent
from agents.rules_agent import RulesAgent
from agents.decision_agent import DecisionAgent
from agents.trace_agent import TraceAgent
from managers.state_manager import StateManager, StateManagerConfig
from managers.cache_manager import CacheManager, CacheManagerConfig
from managers.character_manager import CharacterManager, CharacterManagerConfig
from managers.trace_manager import TraceManager
from managers.agent_manager import AgentManager, AgentManagerConfig
from config.core_config import ComponentConfig
from config.agent_config import (
    NarratorConfig, RulesConfig, 
    DecisionConfig, TraceConfig
)

# Type for game components
GameComponent = Union[
    NarratorAgent, RulesAgent, DecisionAgent, TraceAgent,
    StateManager, CacheManager, CharacterManager, TraceManager, AgentManager
]

class GameConfig(ComponentConfig[GameComponent]):
    """Configuration for game components."""
    content_dir: str = Field(
        default=os.getenv("CONTENT_DIR", "data/sections"),
        description="Directory containing section content"
    )
    cache_dir: str = Field(
        default=os.getenv("CACHE_DIR", "data/cache"),
        description="Directory for caching"
    )
    rules_dir: str = Field(
        default=os.getenv("RULES_DIR", "data/rules"),
        description="Directory containing rules files"
    )
    trace_dir: str = Field(
        default=os.getenv("TRACE_DIR", "data/trace"),
        description="Directory containing trace files"
    )
    
    # Model configurations
    model_configs: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: {
            "narrator": {"model_name": os.getenv("NARRATOR_MODEL", "gpt-4o-mini")},
            "rules": {"model_name": os.getenv("RULES_MODEL", "gpt-4o-mini")},
            "decision": {"model_name": os.getenv("DECISION_MODEL", "gpt-4o-mini")},
            "trace": {"model_name": os.getenv("TRACE_MODEL", "gpt-4o-mini")}
        },
        description="Model configurations for each agent"
    )
    
    @model_validator(mode='after')
    def setup_dependencies(self) -> 'GameConfig':
        """Configure component dependencies."""
        from config.agent_config import (
            NarratorConfig, RulesConfig, 
            DecisionConfig, TraceConfig
        )
        from managers.character_manager import CharacterManagerConfig
        from managers.state_manager import StateManagerConfig
        from managers.cache_manager import CacheManagerConfig
        from managers.agent_manager import AgentManagerConfig
        
        # Get base directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Initialize configurations
        self.options.update({
            "narrator_config": NarratorConfig(**self.model_configs["narrator"]),
            "rules_config": RulesConfig(**self.model_configs["rules"]),
            "decision_config": DecisionConfig(**self.model_configs["decision"]),
            "trace_config": TraceConfig(
                model_name=self.model_configs["trace"]["model_name"],
                trace_dir=os.path.join(base_dir, self.trace_dir)
            ),
            "state_manager_config": StateManagerConfig(),
            "cache_manager_config": CacheManagerConfig(
                content_dir=os.path.join(base_dir, self.content_dir),
                cache_dir=os.path.join(base_dir, self.cache_dir),
                rules_dir=os.path.join(base_dir, self.rules_dir)
            ),
            "character_manager_config": CharacterManagerConfig(),
            "agent_manager_config": AgentManagerConfig()
        })
        return self

class GameFactory(BaseModel):
    """Factory for game components initialization."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    config: GameConfig
    
    @cached_property
    def cache_manager(self) -> CacheManager:
        """Initialize CacheManager."""
        return CacheManager(
            config=self.config.options["cache_manager_config"]
        )

    @cached_property
    def character_manager(self) -> CharacterManager:
        """Initialize CharacterManager."""
        return CharacterManager(
            config=self.config.options["character_manager_config"]
        )

    @cached_property
    def trace_manager(self) -> TraceManager:
        """Initialize TraceManager."""
        return TraceManager(
            trace_config=self.config.options["trace_config"]
        )

    @cached_property
    def state_manager(self) -> StateManager:
        """Initialize StateManager with dependencies."""
        return StateManager(
            config=self.config.options["state_manager_config"],
            cache_manager=self.cache_manager,
            character_manager=self.character_manager,
            trace_manager=self.trace_manager
        )

    @cached_property
    def agent_manager(self) -> AgentManager:
        """Initialize AgentManager with dependencies."""
        return AgentManager(
            config=self.config.options["agent_manager_config"],
            state_manager=self.state_manager,
            cache_manager=self.cache_manager,
            character_manager=self.character_manager,
            trace_manager=self.trace_manager
        )

    @cached_property
    def narrator_agent(self) -> NarratorAgent:
        """Initialize NarratorAgent with dependencies."""
        return NarratorAgent(
            config=self.config.options["narrator_config"],
            cache_manager=self.cache_manager,
            state_manager=self.state_manager
        )

    @cached_property
    def rules_agent(self) -> RulesAgent:
        """Initialize RulesAgent with dependencies."""
        return RulesAgent(
            config=self.config.options["rules_config"],
            cache_manager=self.cache_manager,
            state_manager=self.state_manager
        )

    @cached_property
    def decision_agent(self) -> DecisionAgent:
        """Initialize DecisionAgent with dependencies."""
        return DecisionAgent(
            config=self.config.options["decision_config"],
            cache_manager=self.cache_manager,
            state_manager=self.state_manager
        )

    @cached_property
    def trace_agent(self) -> TraceAgent:
        """Initialize TraceAgent with dependencies."""
        return TraceAgent(
            config=self.config.options["trace_config"],
            cache_manager=self.cache_manager,
            state_manager=self.state_manager
        )
