"""Tests for the trace agent module."""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from agents.trace_agent import TraceAgent
from config.agents.trace_agent_config import TraceAgentConfig
from models.game_state import GameState
from models.trace_model import TraceModel, TraceAction, ActionType
from models.errors_model import TraceError

@pytest.fixture
def mock_trace_manager():
    """Create a mock trace manager."""
    manager = Mock()
    manager.record_state = AsyncMock()
    manager.analyze_state = AsyncMock()
    manager.get_current_trace = AsyncMock()
    return manager

@pytest.fixture
def config():
    """Create a test trace agent config."""
    return TraceAgentConfig()

@pytest_asyncio.fixture
async def trace_agent(config, mock_trace_manager):
    """Create a test trace agent."""
    agent = TraceAgent(config=config, trace_manager=mock_trace_manager)
    return agent

@pytest.fixture
def sample_game_state():
    """Create a sample game state."""
    return GameState(
        section_number=1,
        player_input="test input",
        last_update=datetime.now()
    )

@pytest.fixture
def sample_trace_model():
    """Create a sample trace model."""
    return TraceModel(
        session_id="test_session",
        start_time=datetime.now(),
        history=[
            TraceAction(
                timestamp=datetime.now(),
                section=1,
                action_type=ActionType.USER_INPUT,
                details={"input": "test input"}
            )
        ]
    )

@pytest.mark.asyncio
async def test_record_state(trace_agent, mock_trace_manager, sample_game_state):
    """Test recording game state."""
    # Setup mock
    mock_trace_manager.record_state.return_value = None
    
    # Record state
    result = await trace_agent.record_state(sample_game_state)
    
    # Verify result
    assert result is None
    
    # Verify manager calls
    mock_trace_manager.record_state.assert_called_once_with(sample_game_state)

@pytest.mark.asyncio
async def test_analyze_state(trace_agent, mock_trace_manager, sample_game_state):
    """Test analyzing game state."""
    # Setup mock
    mock_trace_manager.analyze_state.return_value = sample_game_state
    
    # Analyze state
    result = await trace_agent.analyze_state(sample_game_state)
    
    # Verify result
    assert isinstance(result, GameState)
    assert result.section_number == sample_game_state.section_number
    
    # Verify manager calls
    mock_trace_manager.analyze_state.assert_called_once_with(sample_game_state)

@pytest.mark.asyncio
async def test_record_state_error(trace_agent, mock_trace_manager, sample_game_state):
    """Test recording state with error."""
    # Setup mock
    mock_trace_manager.record_state.side_effect = Exception("Record error")
    
    # Record state
    result = await trace_agent.record_state(sample_game_state)
    
    # Verify result
    assert isinstance(result, TraceError)
    assert "record error" in result.message.lower()

@pytest.mark.asyncio
async def test_analyze_state_error(trace_agent, mock_trace_manager, sample_game_state):
    """Test analyzing state with error."""
    # Setup mock
    mock_trace_manager.analyze_state.side_effect = Exception("Analysis error")
    
    # Analyze state
    result = await trace_agent.analyze_state(sample_game_state)
    
    # Verify result
    assert isinstance(result, GameState)
    assert result.error
    assert "analysis error" in result.error.lower()

@pytest.mark.asyncio
async def test_create_action_from_state(trace_agent, sample_game_state):
    """Test action creation from game state."""
    # Create action
    action = trace_agent._create_action_from_state(sample_game_state)
    
    # Verify action
    assert isinstance(action, TraceAction)
    assert action.section == sample_game_state.section_number
    assert action.action_type == ActionType.USER_INPUT
    assert action.details["input"] == sample_game_state.player_input

@pytest.mark.asyncio
async def test_determine_action_type(trace_agent, sample_game_state):
    """Test action type determination."""
    # Test user input
    action_type = trace_agent._determine_action_type(sample_game_state)
    assert action_type == ActionType.USER_INPUT
    
    # Test error
    sample_game_state.error = "Test error"
    action_type = trace_agent._determine_action_type(sample_game_state)
    assert action_type == ActionType.ERROR
