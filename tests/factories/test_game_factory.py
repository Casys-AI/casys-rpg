"""Tests for game factory."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from agents.factories.game_factory import GameFactory
from config.game_config import GameConfig
from models.game_state import GameState
from models.character_model import CharacterModel, CharacterStats
from models.narrator_model import NarratorModel
from models.rules_model import RulesModel
from models.decision_model import DecisionModel
from models.trace_model import TraceModel

@pytest.fixture
def mock_game_config() -> GameConfig:
    """Create a mock game config."""
    config = GameConfig()
    config.game_id = "test_game"
    config.session_id = "test_session"
    return config

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
        choices={"1": "Test choice"}
    )

@pytest.fixture
def mock_trace_model() -> TraceModel:
    """Create a mock trace model."""
    return TraceModel(
        section_number=1,
        history=["Test action"]
    )

@pytest.mark.asyncio
async def test_game_factory_create_state():
    """Test creating a game state."""
    # Arrange
    config = GameConfig()
    game_factory = GameFactory()
    
    # Act
    game_state = await game_factory.create_state(config)
    
    # Assert
    assert isinstance(game_state, GameState)
    assert game_state.game_id == config.game_id
    assert game_state.session_id == config.session_id

@pytest.mark.asyncio
async def test_game_factory_create_state_with_models(
    mock_character_model,
    mock_narrator_model,
    mock_rules_model,
    mock_decision_model,
    mock_trace_model
):
    """Test creating a game state with all models."""
    # Arrange
    config = GameConfig()
    game_factory = GameFactory()
    
    # Act
    game_state = await game_factory.create_state(
        config,
        character=mock_character_model,
        narrator=mock_narrator_model,
        rules=mock_rules_model,
        decision=mock_decision_model,
        trace=mock_trace_model
    )
    
    # Assert
    assert game_state.character == mock_character_model
    assert game_state.narrative == mock_narrator_model
    assert game_state.rules == mock_rules_model
    assert game_state.decision == mock_decision_model
    assert game_state.trace == mock_trace_model

@pytest.mark.asyncio
async def test_game_factory_error_handling():
    """Test error handling in game factory."""
    # Arrange
    config = GameConfig()
    config.game_id = ""  # Invalid game_id
    game_factory = GameFactory()
    
    # Act & Assert
    with pytest.raises(ValueError):
        await game_factory.create_state(config)
