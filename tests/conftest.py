import pytest
import os
import sys
import pytest_asyncio
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Ajouter le répertoire racine au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class AsyncIterMock:
    """Mock that returns an async iterator."""
    def __init__(self, items):
        self.items = items
        self._iter = iter(items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration

class AsyncMockWithIter(AsyncMock):
    """Mock that can return an async iterator."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._iter_items = []
        self._iter_mock = None

    def set_iter_items(self, items):
        """Set items to yield."""
        self._iter_items = items
        self._iter_mock = AsyncIterMock(items)
        self.ainvoke.return_value = self._iter_mock

@pytest_asyncio.fixture(scope="function")
async def event_loop():
    """Create a new event loop for each test function."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def clean_event_bus():
    """Provide a clean event bus for each test."""
    from event_bus import EventBus
    event_bus = EventBus()
    yield event_bus

@pytest.fixture(scope="session")
def base_config():
    """Create base configuration for tests."""
    from config.game_config import GameConfig
    from config.storage_config import StorageConfig
    config = GameConfig.create_default()
    config.manager_configs.storage_config = StorageConfig(base_path=Path("./test_data"))
    return config

@pytest.fixture(scope="session")
def base_managers(base_config):
    """Create base managers for tests."""
    from managers.cache_manager import CacheManager
    from managers.state_manager import StateManager
    from managers.rules_manager import RulesManager
    from managers.narrator_manager import NarratorManager
    from managers.trace_manager import TraceManager
    from managers.workflow_manager import WorkflowManager
    
    managers = MagicMock()
    managers.cache_manager = AsyncMock(spec=CacheManager)
    managers.state_manager = AsyncMock(spec=StateManager)
    managers.rules_manager = AsyncMock(spec=RulesManager)
    managers.narrator_manager = AsyncMock(spec=NarratorManager)
    managers.trace_manager = AsyncMock(spec=TraceManager)
    managers.workflow_manager = AsyncMock(spec=WorkflowManager)
    return managers

@pytest.fixture(scope="session")
def base_agents(base_managers):
    """Create base agents for tests."""
    agents = MagicMock()
    agents.rules_agent = AsyncMock()
    agents.narrator_agent = AsyncMock()
    agents.trace_agent = AsyncMock()
    return agents

@pytest.fixture
def mock_managers():
    """Create mock managers for testing."""
    from models.types.game_types import GameManagers
    
    state_manager = AsyncMock()
    rules_manager = AsyncMock()
    decision_manager = AsyncMock()
    trace_manager = AsyncMock()
    cache_manager = AsyncMock()
    narrator_manager = AsyncMock()
    workflow_manager = AsyncMock()
    character_manager = AsyncMock()
    
    managers = GameManagers(
        state_manager=state_manager,
        rules_manager=rules_manager,
        decision_manager=decision_manager,
        trace_manager=trace_manager,
        cache_manager=cache_manager,
        narrator_manager=narrator_manager,
        workflow_manager=workflow_manager,
        character_manager=character_manager
    )
    
    return managers

@pytest.fixture
def mock_agents():
    """Create mock agents for testing."""
    from models.types.game_types import GameAgents
    
    decision_agent = AsyncMockWithIter()
    rules_agent = AsyncMockWithIter()
    narrator_agent = AsyncMockWithIter()
    trace_agent = AsyncMockWithIter()
    
    agents = GameAgents(
        decision_agent=decision_agent,
        rules_agent=rules_agent,
        narrator_agent=narrator_agent,
        trace_agent=trace_agent
    )
    
    return agents

@pytest.fixture
def mock_agent_manager(mock_agents, mock_managers):
    """Create a mock agent manager for testing."""
    from managers.agent_manager import AgentManager
    from config.agents.agent_config_base import AgentConfigBase
    
    agent_manager = AgentManager(
        agents=mock_agents,
        managers=mock_managers,
        story_graph_config=AgentConfigBase()
    )
    
    return agent_manager
