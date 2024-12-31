"""Tests for game factory."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from pathlib import Path

from config.game_config import GameConfig, ManagerConfigs
from config.game_constants import GameMode
from models.game_state import GameState
from models.character_model import CharacterModel, CharacterStats
from models.narrator_model import NarratorModel
from models.rules_model import RulesModel
from models.decision_model import DecisionModel
from models.trace_model import TraceModel
from config.storage_config import StorageConfig

@pytest.fixture
def mock_game_config() -> GameConfig:
    """Create a mock game config."""
    storage_config = StorageConfig(base_path=Path("./test_data"))
    manager_configs = ManagerConfigs(storage_config=storage_config)
    return GameConfig(
        mode=GameMode.NORMAL,
        manager_configs=manager_configs
    )

@pytest.fixture
def mock_character_model() -> CharacterModel:
    """Create a mock character model."""
    return CharacterModel(
        name="Test Character",
        stats=CharacterStats(SKILL=10, STAMINA=20, LUCK=5),
        inventory=["sword", "potion"]
    )

@pytest.fixture
def mock_narrator_model() -> NarratorModel:
    """Create a mock narrator model."""
    return NarratorModel(
        section_number=1,
        content="Test narrative content"
    )

@pytest.fixture
def mock_rules_model() -> RulesModel:
    """Create a mock rules model."""
    return RulesModel(
        section_number=1,
        rules={"test_rule": "Test rule description"}
    )

@pytest.fixture
def mock_decision_model() -> DecisionModel:
    """Create a mock decision model."""
    return DecisionModel(
        section_number=1,
        choices=["choice1", "choice2"],
        conditions=["condition1"]
    )

@pytest.fixture
def mock_trace_model() -> TraceModel:
    """Create a mock trace model."""
    return TraceModel(
        section_number=1,
        actions=["action1", "action2"]
    )

@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager."""
    return AsyncMock()

@pytest.fixture
def mock_state_manager():
    """Create a mock state manager."""
    return AsyncMock()

@patch('agents.factories.game_factory.CacheManager')
@patch('agents.factories.game_factory.StateManager')
@patch('agents.factories.game_factory.CharacterManager')
@patch('agents.factories.game_factory.TraceManager')
@patch('agents.factories.game_factory.RulesManager')
@patch('agents.factories.game_factory.DecisionManager')
@patch('agents.factories.game_factory.NarratorManager')
@patch('agents.factories.game_factory.WorkflowManager')
def test_game_factory_create_state(
    mock_workflow_manager,
    mock_narrator_manager,
    mock_decision_manager,
    mock_rules_manager,
    mock_trace_manager,
    mock_character_manager,
    mock_state_manager,
    mock_cache_manager,
    mock_game_config
):
    """Test creating a game state."""
    from agents.factories.game_factory import GameFactory
    
    # Setup
    factory = GameFactory(mock_game_config)
    
    # Test
    components = factory.create_game_components()
    
    # Verify
    assert components is not None
    assert len(components) == 2  # agents and managers
    agents, managers = components
    assert isinstance(agents, dict)
    assert isinstance(managers, dict)

@patch('agents.factories.game_factory.CacheManager')
@patch('agents.factories.game_factory.StateManager')
@patch('agents.factories.game_factory.CharacterManager')
@patch('agents.factories.game_factory.TraceManager')
@patch('agents.factories.game_factory.RulesManager')
@patch('agents.factories.game_factory.DecisionManager')
@patch('agents.factories.game_factory.NarratorManager')
@patch('agents.factories.game_factory.WorkflowManager')
def test_game_factory_create_state_with_models(
    mock_workflow_manager,
    mock_narrator_manager,
    mock_decision_manager,
    mock_rules_manager,
    mock_trace_manager,
    mock_character_manager,
    mock_state_manager,
    mock_cache_manager,
    mock_character_model,
    mock_narrator_model,
    mock_rules_model,
    mock_decision_model,
    mock_trace_model,
    mock_game_config
):
    """Test creating a game state with all models."""
    from agents.factories.game_factory import GameFactory
    
    # Setup
    factory = GameFactory(mock_game_config)
    
    # Configure mocks
    mock_state_manager.return_value.get_current_state.return_value = GameState(
        character=mock_character_model,
        narrator=mock_narrator_model,
        rules=mock_rules_model,
        decision=mock_decision_model,
        trace=mock_trace_model
    )
    
    # Test
    components = factory.create_game_components()
    
    # Verify
    agents, managers = components
    assert isinstance(agents, dict)
    assert isinstance(managers, dict)
    
    # Verify managers were created with correct config
    mock_cache_manager.assert_called_once()
    mock_state_manager.assert_called_once()
    mock_character_manager.assert_called_once()
    mock_trace_manager.assert_called_once()
    mock_rules_manager.assert_called_once()
    mock_decision_manager.assert_called_once()
    mock_narrator_manager.assert_called_once()
    mock_workflow_manager.assert_called_once()

@patch('agents.factories.game_factory.CacheManager')
def test_game_factory_error_handling(mock_cache_manager, mock_game_config):
    """Test error handling in game factory."""
    from agents.factories.game_factory import GameFactory
    
    # Setup error condition
    mock_cache_manager.side_effect = Exception("Test error")
    
    # Test
    with pytest.raises(Exception) as exc_info:
        factory = GameFactory(mock_game_config)
        
    assert str(exc_info.value) == "Test error"
