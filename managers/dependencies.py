"""
Dependencies for FastAPI.
"""
from typing import Optional
from loguru import logger
from agents.factories.game_factory import GameFactory, GameAgents, GameManagers
from managers.agent_manager import AgentManager

# Composants du jeu
_game_factory: GameFactory | None = None
_agent_manager: AgentManager | None = None
_game_components: tuple[GameAgents, GameManagers] | None = None

def get_agent_manager() -> AgentManager:
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
