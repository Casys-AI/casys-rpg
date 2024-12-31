"""Manager-specific test fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
from datetime import datetime

from models.types.manager_types import GameManagers
from models.types.agent_types import GameAgents
from managers.agent_manager import AgentManager
from managers.cache_manager import CacheManager
from managers.state_manager import StateManager
from managers.rules_manager import RulesManager
from managers.narrator_manager import NarratorManager
from managers.trace_manager import TraceManager
from managers.workflow_manager import WorkflowManager
from managers.character_manager import CharacterManager
from managers.decision_manager import DecisionManager
from config.agents.agent_config_base import AgentConfigBase
from config.game_config import GameConfig
from config.storage_config import StorageConfig
from agents.factories.game_factory import GameFactory

@pytest.fixture(scope="session")
def base_config():
    """Create base configuration for tests."""
    config = GameConfig.create_default()
    config.manager_configs.storage_config = StorageConfig(base_path=Path("./test_data"))
    return config

@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager."""
    manager = AsyncMock(spec=CacheManager)
    manager.get = AsyncMock(return_value=None)
    manager.set = AsyncMock()
    manager.delete = AsyncMock()
    return manager

@pytest.fixture
def mock_state_manager():
    """Create a mock state manager."""
    manager = AsyncMock(spec=StateManager)
    manager.get_state = AsyncMock()
    manager.save_state = AsyncMock()
    manager.update_state = AsyncMock()
    return manager

@pytest.fixture
def mock_rules_manager():
    """Create a mock rules manager."""
    manager = AsyncMock(spec=RulesManager)
    manager.get_rules = AsyncMock()
    manager.validate_rules = AsyncMock()
    manager.process_rules = AsyncMock()
    return manager

@pytest.fixture
def mock_decision_manager():
    """Create a mock decision manager."""
    manager = AsyncMock(spec=DecisionManager)
    manager.get_choices = AsyncMock()
    manager.validate_choice = AsyncMock()
    manager.process_choice = AsyncMock()
    return manager

@pytest.fixture
def mock_character_manager():
    """Create a mock character manager."""
    manager = AsyncMock(spec=CharacterManager)
    manager.get_character = AsyncMock()
    manager.update_character = AsyncMock()
    manager.validate_character = AsyncMock()
    return manager

@pytest.fixture
def mock_workflow_manager():
    """Create a mock workflow manager."""
    manager = AsyncMock(spec=WorkflowManager)
    manager.get_workflow = AsyncMock()
    manager.execute_workflow = AsyncMock()
    manager.validate_workflow = AsyncMock()
    return manager

@pytest.fixture
def mock_trace_manager():
    """Create a mock trace manager."""
    manager = AsyncMock(spec=TraceManager)
    manager.add_trace = AsyncMock()
    manager.get_traces = AsyncMock()
    return manager

@pytest.fixture
def mock_managers(
    mock_cache_manager,
    mock_state_manager,
    mock_rules_manager,
    mock_decision_manager,
    mock_character_manager,
    mock_workflow_manager,
    mock_trace_manager
):
    """Create all mock managers."""
    return GameManagers(
        cache_manager=mock_cache_manager,
        state_manager=mock_state_manager,
        rules_manager=mock_rules_manager,
        decision_manager=mock_decision_manager,
        character_manager=mock_character_manager,
        workflow_manager=mock_workflow_manager,
        trace_manager=mock_trace_manager
    )

@pytest.fixture
def mock_agents():
    """Create mock agents for testing."""
    decision_agent = AsyncMock()
    rules_agent = AsyncMock()
    narrator_agent = AsyncMock()
    trace_agent = AsyncMock()
    
    return GameAgents(
        decision_agent=decision_agent,
        rules_agent=rules_agent,
        narrator_agent=narrator_agent,
        trace_agent=trace_agent
    )

@pytest.fixture
def mock_agent_manager(mock_agents, mock_managers, base_config):
    """Create a mock agent manager."""
    game_factory = GameFactory(config=base_config)
    
    return AgentManager(
        agents=mock_agents,
        managers=mock_managers,
        game_factory=game_factory,
        story_graph_config=AgentConfigBase()
    )
