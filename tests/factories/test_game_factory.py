"""Tests for the game factory module."""
import pytest
from unittest.mock import patch, Mock

from agents.factories.game_factory import GameFactory

@pytest.fixture
def game_factory(base_config):
    """Create a game factory instance."""
    with patch('agents.factories.game_factory.CacheManager') as mock_cache:
        factory = GameFactory(config=base_config)
        factory._cache_manager = mock_cache.return_value
        return factory

@pytest.mark.asyncio
async def test_create_game_instance(game_factory, base_managers):
    """Test creation of complete game instance."""
    with patch.multiple(
        'agents.factories.game_factory',
        NarratorManager=Mock(return_value=base_managers.narrator_manager),
        RulesManager=Mock(return_value=base_managers.rules_manager),
        TraceManager=Mock(return_value=base_managers.trace_manager),
        StateManager=Mock(return_value=base_managers.state_manager),
        WorkflowManager=Mock(return_value=base_managers.workflow_manager)
    ):
        agents, managers = await game_factory.create_game_components()
        assert agents is not None
        assert managers is not None
        assert managers.narrator_manager == base_managers.narrator_manager
        assert managers.rules_manager == base_managers.rules_manager
        assert managers.trace_manager == base_managers.trace_manager

@pytest.mark.asyncio
async def test_create_story_graph(game_factory, base_managers):
    """Test creation of story graph."""
    with patch.multiple(
        'agents.factories.game_factory',
        StateManager=Mock(return_value=base_managers.state_manager),
        WorkflowManager=Mock(return_value=base_managers.workflow_manager)
    ):
        graph = await game_factory.create_story_graph()
        assert graph is not None
        assert graph._managers.state_manager == base_managers.state_manager
        assert graph._managers.workflow_manager == base_managers.workflow_manager

def test_invalid_config():
    """Test factory creation with invalid config."""
    with pytest.raises(ValueError):
        GameFactory(config=None)

@patch('agents.factories.game_factory.CacheManager', side_effect=ValueError)
def test_invalid_cache_manager(mock_cache, base_config):
    """Test factory creation with invalid cache manager."""
    with pytest.raises(ValueError):
        GameFactory(config=base_config)
