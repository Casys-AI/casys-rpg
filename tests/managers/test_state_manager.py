"""Tests for the state manager module."""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime
import uuid

from managers.state_manager import StateManager
from config.storage_config import StorageConfig
from models.game_state import GameState
from models.errors_model import StateError
from managers.protocols.character_manager_protocol import CharacterManagerProtocol

@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager."""
    cache = Mock()
    cache.save_cached_content = AsyncMock()
    cache.get_cached_content = AsyncMock()
    return cache

@pytest.fixture
def mock_character_manager():
    """Create a mock character manager."""
    manager = Mock(spec=CharacterManagerProtocol)
    manager.save_character = Mock()
    manager.load_character = Mock()
    return manager

@pytest.fixture
def config():
    """Create a test storage config."""
    return StorageConfig.get_default_config(base_path="./test_data")

@pytest_asyncio.fixture
async def state_manager(config, mock_cache_manager, mock_character_manager):
    """Create and initialize a test state manager."""
    manager = StateManager(
        config=config, 
        cache_manager=mock_cache_manager,
        character_manager=mock_character_manager
    )
    await manager.initialize()  # Initialize the manager
    return manager

@pytest.fixture
def sample_game_state():
    """Create a sample game state."""
    return GameState(
        section_number=1,
        player_input="test input",
        last_update=datetime.now()
    )

@pytest.mark.asyncio
async def test_game_id_generation(state_manager):
    """Test that game_id is generated and consistent."""
    # game_id should be already set after initialization
    game_id = state_manager.game_id
    assert isinstance(game_id, str)
    assert uuid.UUID(game_id)  # Should be a valid UUID
    
    # Second access should return the same ID
    assert state_manager.game_id == game_id
    
    # Config should have the game_id set
    assert state_manager.config.game_id == game_id

@pytest.mark.asyncio
async def test_save_state(state_manager, sample_game_state, mock_cache_manager):
    """Test saving game state."""
    # Configure mock to return success
    mock_cache_manager.save_cached_content.return_value = True
    
    # Save the state
    saved_state = await state_manager.save_state(sample_game_state)
    
    # Check that cache_manager was called correctly
    mock_cache_manager.save_cached_content.assert_called_once()
    call_args = mock_cache_manager.save_cached_content.call_args[1]
    assert call_args["namespace"] == "state"
    assert call_args["key"] == f"section_{sample_game_state.section_number}"
    
    # Check that state was saved internally
    assert state_manager.current_state == saved_state
    assert saved_state in state_manager.state_history

@pytest.mark.asyncio
async def test_load_state(state_manager, sample_game_state, mock_cache_manager):
    """Test loading game state."""
    # Setup mock to return serialized state
    mock_cache_manager.get_cached_content.return_value = state_manager._serialize_state(sample_game_state)
    
    # Load the state
    loaded_state = await state_manager.load_state(sample_game_state.section_number)
    
    # Check that cache_manager was called correctly
    mock_cache_manager.get_cached_content.assert_called_once_with(
        key=f"section_{sample_game_state.section_number}",
        namespace="state"
    )
    
    # Check that loaded state matches original
    assert loaded_state.section_number == sample_game_state.section_number
    assert loaded_state.player_input == sample_game_state.player_input
    
    # Check that current state was updated
    assert state_manager.current_state == loaded_state

@pytest.mark.asyncio
async def test_load_nonexistent_state(state_manager, mock_cache_manager):
    """Test loading a state that doesn't exist."""
    # Setup mock to return None
    mock_cache_manager.get_cached_content.return_value = None
    
    # Load should return None for non-existent state
    loaded_state = await state_manager.load_state(999)
    assert loaded_state is None
    
    # Current state should not be changed
    assert state_manager.current_state is None

@pytest.mark.asyncio
async def test_create_initial_state(state_manager):
    """Test creating initial state."""
    initial_state = await state_manager.create_initial_state()
    assert initial_state.section_number == 1
    assert initial_state.error is None
    assert state_manager.current_state == initial_state

@pytest.mark.asyncio
async def test_create_error_state(state_manager):
    """Test creating error state."""
    error_message = "Test error"
    error_state = await state_manager.create_error_state(error_message)
    assert error_state.error == error_message
    assert error_state.section_number == 1  # Should be 1 as no current state
    assert state_manager.current_state == error_state

@pytest.mark.asyncio
async def test_state_validation(state_manager):
    """Test state validation."""
    # Valid state
    valid_state = GameState(section_number=1)
    assert state_manager.validate_state(valid_state)
    
    # None state
    assert not state_manager.validate_state(None)
    
    # Try to validate invalid state without creating it
    assert not state_manager.validate_state({"section_number": 0})
