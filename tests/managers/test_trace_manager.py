"""Tests for the trace manager module."""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from managers.trace_manager import TraceManager
from models.game_state import GameState
from models.trace_model import TraceModel, TraceAction, ActionType
from config.storage_config import StorageConfig
from models.errors_model import TraceError

@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager."""
    cache = Mock()
    cache.save_cached_content = AsyncMock()
    return cache

@pytest.fixture
def config():
    """Create a test storage config."""
    return StorageConfig.get_default_config(base_path="./test_data")

@pytest_asyncio.fixture
async def trace_manager(config, mock_cache_manager):
    """Create a test trace manager."""
    manager = TraceManager(config=config, cache_manager=mock_cache_manager)
    return manager

@pytest.fixture
def sample_game_state():
    """Create a sample game state."""
    return GameState(
        section_number=1,
        player_input="test input",
        last_update=datetime.now()
    )

@pytest.fixture
def sample_action():
    """Create a sample action."""
    return {
        "type": ActionType.USER_INPUT,
        "input": "test input",
        "timestamp": datetime.now().isoformat()
    }

@pytest.mark.asyncio
async def test_start_session(trace_manager, mock_cache_manager):
    """Test starting a new session."""
    await trace_manager.start_session()
    
    # Verify trace was initialized
    assert trace_manager._current_trace is not None
    assert isinstance(trace_manager._current_trace, TraceModel)
    assert trace_manager._current_trace.session_id != ""
    assert len(trace_manager._current_trace.history) == 0
    
    # Verify save was called
    mock_cache_manager.save_cached_content.assert_called_once()

@pytest.mark.asyncio
async def test_process_trace(trace_manager, mock_cache_manager, sample_game_state, sample_action):
    """Test processing a trace."""
    # Process a trace
    await trace_manager.process_trace(sample_game_state, sample_action)
    
    # Verify trace was created and action added
    assert trace_manager._current_trace is not None
    assert len(trace_manager._current_trace.history) == 1
    
    action = trace_manager._current_trace.history[0]
    assert isinstance(action, TraceAction)
    assert action.section == sample_game_state.section_number
    assert action.action_type == sample_action["type"]
    assert action.details == sample_action
    
    # Verify save was called
    mock_cache_manager.save_cached_content.assert_called()

@pytest.mark.asyncio
async def test_save_trace(trace_manager, mock_cache_manager):
    """Test saving trace to storage."""
    # Start session
    await trace_manager.start_session()
    
    # Configure mock
    mock_cache_manager.save_cached_content.return_value = True
    
    # Test successful save
    await trace_manager.save_trace()
    mock_cache_manager.save_cached_content.assert_called()
    
    # Test save with no trace
    trace_manager._current_trace = None
    await trace_manager.save_trace()  # Should not raise error

@pytest.mark.asyncio
async def test_get_current_trace(trace_manager):
    """Test getting current trace."""
    # No trace initially
    current_trace = await trace_manager.get_current_trace()
    assert current_trace is None
    
    # After starting session
    await trace_manager.start_session()
    current_trace = await trace_manager.get_current_trace()
    assert current_trace is not None
    assert isinstance(current_trace, TraceModel)