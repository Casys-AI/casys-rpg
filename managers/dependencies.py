"""
Dependencies for FastAPI.
"""
from typing import Optional, Dict, Union
from loguru import logger

from agents.factories.game_factory import GameFactory
from managers.protocols.agent_manager_protocol import AgentManagerProtocol
from managers.protocols.state_manager_protocol import StateManagerProtocol
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
from managers.protocols.character_manager_protocol import CharacterManagerProtocol
from managers.protocols.trace_manager_protocol import TraceManagerProtocol
from managers.protocols.decision_manager_protocol import DecisionManagerProtocol
from managers.protocols.rules_manager_protocol import RulesManagerProtocol
from managers.protocols.narrator_manager_protocol import NarratorManagerProtocol
from managers.protocols.workflow_manager_protocol import WorkflowManagerProtocol

from agents.protocols.story_graph_protocol import StoryGraphProtocol
from agents.protocols.narrator_agent_protocol import NarratorAgentProtocol
from agents.protocols.rules_agent_protocol import RulesAgentProtocol
from agents.protocols.decision_agent_protocol import DecisionAgentProtocol
from agents.protocols.trace_agent_protocol import TraceAgentProtocol
from agents.protocols.base_agent_protocol import BaseAgentProtocol

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

# Composants du jeu
_game_factory: Optional[GameFactory] = None
_agent_manager: Optional[AgentManagerProtocol] = None
_game_components: Optional[tuple[Dict[str, AgentProtocols], Dict[str, ManagerProtocols]]] = None

def get_agent_manager() -> AgentManagerProtocol:
    """Get AgentManager instance."""
    global _agent_manager, _game_factory, _game_components
    
    if not _agent_manager:
        logger.info("Creating new AgentManager instance")
        if not _game_factory:
            logger.debug("Creating new GameFactory instance")
            _game_factory = GameFactory()
        
        if not _game_components:
            logger.debug("Creating game components")
            _game_components = _game_factory.create_game_components()
            
        agents, managers = _game_components
        
        # Import AgentManager here to avoid circular imports
        from managers.agent_manager import AgentManager
        
        logger.debug("Initializing AgentManager with components")
        _agent_manager = AgentManager(
            agents=agents,
            managers=managers,
            game_factory=_game_factory,
            story_graph_config=_game_factory._config.agent_configs.story_graph_config
        )
        logger.info("AgentManager initialized successfully")
    else:
        logger.debug("Returning existing AgentManager instance")
        
    return _agent_manager
