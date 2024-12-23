"""Tests for the game factory module."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from agents.factories.game_factory import GameFactory
from config.game_config import GameConfig
from config.storage_config import StorageConfig
from agents.narrator_agent import NarratorAgent
from agents.rules_agent import RulesAgent
from agents.decision_agent import DecisionAgent
from agents.trace_agent import TraceAgent
from managers.narrator_manager import NarratorManager
from managers.rules_manager import RulesManager
from managers.decision_manager import DecisionManager
from managers.trace_manager import TraceManager
from managers.cache_manager import CacheManager

@pytest.fixture
def mock_config():
    """Create a mock game configuration."""
    config = GameConfig.create_default()
    storage_config = StorageConfig(base_path=Path("./test_data"))
    config.manager_configs.storage_config = storage_config
    return config

@pytest.fixture
def game_factory(mock_config):
    """Create a game factory instance."""
    return GameFactory(config=mock_config)

def test_create_narrator_agent(game_factory):
    """Test creation of narrator agent."""
    agent = game_factory.create_narrator_agent()
    
    assert isinstance(agent, NarratorAgent)
    assert isinstance(agent._manager, NarratorManager)
    assert agent._config.llm is not None
    assert agent._config.system_message is not None

def test_create_rules_agent(game_factory):
    """Test creation of rules agent."""
    agent = game_factory.create_rules_agent()
    
    assert isinstance(agent, RulesAgent)
    assert isinstance(agent._manager, RulesManager)
    assert agent._config.llm is not None
    assert agent._config.system_message is not None

def test_create_decision_agent(game_factory):
    """Test creation of decision agent."""
    agent = game_factory.create_decision_agent()
    
    assert isinstance(agent, DecisionAgent)
    assert isinstance(agent._manager, DecisionManager)
    assert agent._config.llm is not None
    assert agent._config.system_message is not None
    assert "rules_agent" in agent._config.dependencies

def test_create_trace_agent(game_factory):
    """Test creation of trace agent."""
    agent = game_factory.create_trace_agent()
    
    assert isinstance(agent, TraceAgent)
    assert isinstance(agent._manager, TraceManager)
    assert agent._config is not None

def test_create_story_graph(game_factory):
    """Test creation of story graph."""
    graph = game_factory.create_story_graph()
    
    assert graph is not None
    assert hasattr(graph, "process_turn")
    assert len(graph._agents) == 4

def test_create_game_instance(game_factory):
    """Test creation of complete game instance."""
    game = game_factory.create_game()
    
    assert game is not None
    assert game.story_graph is not None
    assert game.config == game_factory._config
    assert hasattr(game, "process_turn")

@patch("factories.game_factory.OpenAI")
def test_create_llm(mock_openai, game_factory):
    """Test LLM creation."""
    llm = game_factory._create_llm()
    
    assert llm is not None
    mock_openai.assert_called_once()
    assert mock_openai.call_args[1]["model"] == game_factory._config.llm_model

def test_create_managers(game_factory):
    """Test creation of all managers."""
    narrator_manager = game_factory._create_narrator_manager()
    rules_manager = game_factory._create_rules_manager()
    decision_manager = game_factory._create_decision_manager()
    trace_manager = game_factory._create_trace_manager()
    
    assert isinstance(narrator_manager, NarratorManager)
    assert isinstance(rules_manager, RulesManager)
    assert isinstance(decision_manager, DecisionManager)
    assert isinstance(trace_manager, TraceManager)

def test_invalid_config():
    """Test factory creation with invalid config."""
    with pytest.raises(ValueError):
        GameFactory(config=None)

def test_invalid_cache_manager(mock_config):
    """Test factory creation with invalid cache manager."""
    with pytest.raises(ValueError):
        GameFactory(config=mock_config, cache_manager=None)
