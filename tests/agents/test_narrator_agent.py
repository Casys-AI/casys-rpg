"""Tests for the narrator agent module."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from agents import NarratorAgent
from agents.protocols import NarratorAgentProtocol
from managers.protocols import NarratorManagerProtocol, CacheManagerProtocol

from models import (
    GameState, NarratorModel, CharacterModel,
    CharacterStats, NarratorError, Inventory, Item
)
from config.agents import NarratorAgentConfig

@pytest.fixture
def mock_narrator_manager() -> NarratorManagerProtocol:
    """Create a mock narrator manager."""
    manager = AsyncMock(spec=NarratorManagerProtocol)
    manager.get_cached_narrative = AsyncMock(return_value=None)
    manager.process_narrative = AsyncMock()
    manager.save_narrative = AsyncMock()
    return manager

@pytest.fixture
def mock_cache_manager() -> CacheManagerProtocol:
    """Create a mock cache manager."""
    manager = AsyncMock(spec=CacheManagerProtocol)
    manager.get_cached_data = AsyncMock(return_value=None)
    manager.save_to_cache = AsyncMock()
    return manager

@pytest.fixture
def narrator_config() -> NarratorAgentConfig:
    """Create a test narrator agent config."""
    config = NarratorAgentConfig()
    config.llm = AsyncMock()
    config.system_message = "Test system message"
    return config

@pytest_asyncio.fixture
async def narrator_agent(narrator_config, mock_narrator_manager) -> NarratorAgentProtocol:
    """Create a test narrator agent."""
    return NarratorAgent(
        config=narrator_config,
        narrator_manager=mock_narrator_manager
    )

@pytest.fixture
def sample_inventory() -> Inventory:
    """Create a sample inventory."""
    return Inventory(items={
        "sword": Item(name="Sword", description="A sharp sword"),
        "potion": Item(name="Potion", description="A healing potion")
    })

@pytest.fixture
def sample_character(sample_inventory) -> CharacterModel:
    """Create a sample character for testing."""
    return CharacterModel(
        name="Test Character",
        stats=CharacterStats(SKILL=10, STAMINA=20, LUCK=5),
        inventory=sample_inventory
    )

@pytest.fixture
def sample_narrator_model() -> NarratorModel:
    """Create a sample narrator model."""
    return NarratorModel(
        section_number=1,
        content="This is a test narrative"
    )

@pytest.fixture
def sample_game_state(sample_character) -> GameState:
    """Create a sample game state."""
    return GameState(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        character=sample_character
    )

@pytest.mark.asyncio
async def test_narrator_agent_initialization(narrator_agent):
    """Test that the narrator agent is initialized correctly."""
    assert narrator_agent is not None
    assert isinstance(narrator_agent, NarratorAgentProtocol)

@pytest.mark.asyncio
async def test_process_narrative_cache_hit(
    narrator_agent, mock_narrator_manager, sample_narrator_model, sample_game_state
):
    """Test processing narrative with cache hit."""
    mock_narrator_manager.get_cached_narrative.return_value = sample_narrator_model
    
    result = await narrator_agent.process_narrative(sample_game_state)
    
    assert result == sample_narrator_model
    mock_narrator_manager.get_cached_narrative.assert_called_once()
    mock_narrator_manager.process_narrative.assert_not_called()

@pytest.mark.asyncio
async def test_process_narrative_cache_miss(
    narrator_agent, mock_narrator_manager, sample_narrator_model, sample_game_state
):
    """Test processing narrative with cache miss."""
    mock_narrator_manager.get_cached_narrative.return_value = None
    mock_narrator_manager.process_narrative.return_value = sample_narrator_model
    
    result = await narrator_agent.process_narrative(sample_game_state)
    
    assert result == sample_narrator_model
    mock_narrator_manager.get_cached_narrative.assert_called_once()
    mock_narrator_manager.process_narrative.assert_called_once()

@pytest.mark.asyncio
async def test_process_narrative_with_context(
    narrator_agent, mock_narrator_manager,
    sample_narrator_model, sample_game_state
):
    """Test narrative processing with character context."""
    mock_narrator_manager.process_narrative.return_value = sample_narrator_model
    
    result = await narrator_agent.process_narrative(sample_game_state)
    
    assert result == sample_narrator_model
    mock_narrator_manager.process_narrative.assert_called_once_with(
        game_state=sample_game_state,
        character=sample_game_state.character
    )

@pytest.mark.asyncio
async def test_process_invalid_state(narrator_agent, sample_game_state):
    """Test processing with invalid state."""
    invalid_state = sample_game_state.model_copy()
    invalid_state.section_number = -1
    
    with pytest.raises(NarratorError):
        await narrator_agent.process_narrative(invalid_state)

@pytest.mark.asyncio
async def test_process_narrative_error(
    narrator_agent, mock_narrator_manager, sample_game_state
):
    """Test narrative processing with error."""
    mock_narrator_manager.process_narrative.side_effect = Exception("Test error")
    
    with pytest.raises(NarratorError):
        await narrator_agent.process_narrative(sample_game_state)
