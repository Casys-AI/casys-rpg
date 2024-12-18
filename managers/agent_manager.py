"""
Agent Manager Module
Handles coordination between different agents and manages game state.
"""

from typing import Dict, Optional, Any, AsyncGenerator, ClassVar
from pydantic import BaseModel, ConfigDict
from langchain.agents import Tool
from models.game_state import GameState
from agents.narrator_agent import NarratorAgent
from agents.rules_agent import RulesAgent
from agents.decision_agent import DecisionAgent
from agents.trace_agent import TraceAgent
from agents.story_graph import StoryGraph
from managers.state_manager import StateManager, StateManagerConfig
from managers.cache_manager import CacheManager
from managers.character_manager import CharacterManager
from managers.trace_manager import TraceManager
from config.agent_config import NarratorConfig, RulesConfig, DecisionConfig, TraceConfig, AgentConfig
import logging

# Type pour l'état du graph
GraphState = Dict[str, Any]

class AgentManagerConfig(BaseModel):
    """Configuration pour AgentManager"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    narrator_agent: Optional[NarratorAgent] = None
    rules_agent: Optional[RulesAgent] = None
    decision_agent: Optional[DecisionAgent] = None
    trace_agent: Optional[TraceAgent] = None
    state_manager: Optional[StateManager] = None
    cache_manager: Optional[CacheManager] = None
    character_manager: Optional[CharacterManager] = None
    trace_manager: Optional[TraceManager] = None

class AgentManager(BaseModel):
    """
    Coordinates different agents and manages their interactions.
    Responsible for:
    1. Initializing and configuring agents
    2. Processing game sections through agent pipeline
    3. Handling user responses
    4. Coordinating between agents and managers
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Configuration
    config: AgentManagerConfig = AgentManagerConfig()
    
    # Managers
    state_manager: StateManager
    cache_manager: CacheManager
    character_manager: CharacterManager
    trace_manager: TraceManager
    
    # Agents
    rules: Optional[RulesAgent] = None
    narrator: Optional[NarratorAgent] = None
    decision: Optional[DecisionAgent] = None
    trace: Optional[TraceAgent] = None
    
    # Story Graph for workflow
    story_graph: Optional[StoryGraph] = None
    
    logger: ClassVar[logging.Logger] = logging.getLogger(__name__)

    def __init__(self, **data):
        """Initialize AgentManager with all components."""
        super().__init__(**data)
        
        # Initialize managers if not provided
        if not self.cache_manager:
            self.cache_manager = CacheManager()
        if not self.character_manager:
            self.character_manager = CharacterManager()
        if not self.trace_manager:
            self.trace_manager = TraceManager()
        if not self.state_manager:
            self.state_manager = StateManager(
                config=StateManagerConfig(
                    cache_manager=self.cache_manager
                )
            )
        
        # Initialize agents with proper configuration
        self.rules = self.config.rules_agent or RulesAgent(
            config=RulesConfig(),
            cache_manager=self.cache_manager
        )
        
        self.narrator = self.config.narrator_agent or NarratorAgent(
            config=NarratorConfig(),
            cache_manager=self.cache_manager
        )
        
        # Create DecisionConfig with RulesAgent dependency
        decision_config = DecisionConfig()
        decision_config.dependencies["rules_agent"] = self.rules
        
        self.decision = self.config.decision_agent or DecisionAgent(
            config=decision_config,
            cache_manager=self.cache_manager
        )
        
        # Create TraceConfig with manager dependencies
        trace_config = TraceConfig()
        trace_config.dependencies.update({
            "trace_manager": self.trace_manager,
            "character_manager": self.character_manager
        })
        
        self.trace = self.config.trace_agent or TraceAgent(
            config=trace_config,
            cache_manager=self.cache_manager
        )
        
        # Initialize StoryGraph with all components
        story_config = AgentConfig()  # Configuration de base pour StoryGraph
        self.story_graph = StoryGraph(
            config=story_config,
            cache_manager=self.cache_manager,
            narrator=self.narrator,
            rules=self.rules,
            decision=self.decision,
            trace=self.trace,
            state_manager=self.state_manager,
            trace_manager=self.trace_manager
        )

    async def process_section(self, section_number: int, content: str) -> Dict:
        """
        Process a complete section through all agents.
        
        Args:
            section_number: Section number to process
            content: Section content
            
        Returns:
            Dict: Updated game state
        """
        try:
            # Use StoryGraph to process the section
            return await self.story_graph.process_section(section_number)
        except Exception as e:
            self.logger.error(f"Error processing section {section_number}: {e}")
            return self.state_manager.create_error_state(str(e))

    async def process_user_response(self, response: str) -> Dict:
        """
        Process user response through decision agent.
        
        Args:
            response: Réponse de l'utilisateur
            
        Returns:
            Dict: État mis à jour
        """
        try:
            # Use StoryGraph to process user input
            return await self.story_graph.process_user_input(response)
        except Exception as e:
            self.logger.error(f"Error processing user response: {e}")
            return self.state_manager.create_error_state(str(e))

    async def process_action(self, action: Dict[str, Any]) -> GameState:
        """Process a user action through the story graph."""
        return await self.story_graph.process_action(action)

    async def get_state(self) -> GameState:
        """Get the current game state."""
        return await self.story_graph.get_state()

    async def stream_state(self) -> AsyncGenerator[GameState, None]:
        """Stream game state updates."""
        async for state in self.story_graph.stream_state():
            yield state

    async def initialize(self):
        """Initialize the story graph."""
        await self.story_graph.initialize()
