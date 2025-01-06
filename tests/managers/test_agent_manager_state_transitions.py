"""Tests for state transitions in AgentManager."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from pathlib import Path

from models.game_state import GameState
from models.decision_model import DecisionModel
from models.errors_model import StateError, GameError
from managers.agent_manager import AgentManager
from config.game_config import GameConfig
from config.storage_config import StorageConfig
from config.manager_configs import ManagerConfigs
from config.game_mode import GameMode
from agents.factories.game_factory import GameFactory

from managers.protocols.state_manager_protocol import StateManagerProtocol
from managers.protocols.workflow_manager_protocol import WorkflowManagerProtocol
from managers.protocols.rules_manager_protocol import RulesManagerProtocol
from managers.protocols.narrator_manager_protocol import NarratorManagerProtocol
from managers.protocols.decision_manager_protocol import DecisionManagerProtocol
from managers.protocols.trace_manager_protocol import TraceManagerProtocol
from managers.protocols.character_manager_protocol import CharacterManagerProtocol
from managers.protocols.cache_manager_protocol import CacheManagerProtocol

@pytest.fixture
def mock_agents():
    """Create mock agents for testing."""
    agents = {
        'story_graph': AsyncMock(),
        'narrator_agent': AsyncMock(),
        'rules_agent': AsyncMock(),
        'decision_agent': AsyncMock(),
        'trace_agent': AsyncMock()
    }
    return agents

@pytest.fixture
def mock_managers():
    """Create mock managers for testing."""
    managers = {
        'state_manager': AsyncMock(spec=StateManagerProtocol),
        'workflow_manager': AsyncMock(spec=WorkflowManagerProtocol),
        'rules_manager': AsyncMock(spec=RulesManagerProtocol),
        'narrator_manager': AsyncMock(spec=NarratorManagerProtocol),
        'decision_manager': AsyncMock(spec=DecisionManagerProtocol),
        'trace_manager': AsyncMock(spec=TraceManagerProtocol),
        'character_manager': AsyncMock(spec=CharacterManagerProtocol),
        'cache_manager': AsyncMock(spec=CacheManagerProtocol)
    }
    return managers

@pytest.fixture
def mock_game_factory():
    """Create a mock game factory."""
    storage_config = StorageConfig(base_path=Path("./test_data"))
    manager_configs = ManagerConfigs(storage_config=storage_config)
    game_config = GameConfig(
        manager_configs=manager_configs,
        mode=GameMode.TEST
    )
    factory = GameFactory(game_config)
    return factory

@pytest.fixture
def agent_manager(mock_agents, mock_managers, mock_game_factory):
    """Create an AgentManager instance with mock dependencies."""
    return AgentManager(
        agents=mock_agents,
        managers=mock_managers,
        game_factory=mock_game_factory
    )

@pytest.mark.asyncio
async def test_state_transition_with_next_section(agent_manager, mock_managers):
    """Test that state transitions correctly when decision includes next_section."""
    # Initial state
    initial_state = GameState(
        session_id="test_session",
        game_id="test_game",
        section_number=1,
        player_input="test_input"
    )
    
    # Mock workflow result with decision containing next_section
    mock_decision = DecisionModel(
        section_number=1,
        next_section=2,
    )
    mock_result = {
        "decision": mock_decision
    }
    
    # Setup mock workflow manager to return our mock result
    mock_managers['workflow_manager'].execute_workflow.return_value = mock_result
    
    # Execute test
    new_state = await agent_manager.process_game_state(initial_state)
    
    # Verify state transition
    assert new_state.section_number == 2
    assert new_state.session_id == initial_state.session_id
    assert new_state.game_id == initial_state.game_id
    assert new_state.player_input is None
    
    # Verify state was saved
    mock_managers['state_manager'].save_state.assert_called_once()
    saved_state = mock_managers['state_manager'].save_state.call_args[0][0]
    assert saved_state.section_number == 2

@pytest.mark.asyncio
async def test_state_transition_without_next_section(agent_manager, mock_managers):
    """Test that state remains unchanged when decision does not include next_section."""
    # Initial state
    initial_state = GameState(
        session_id="test_session",
        game_id="test_game",
        section_number=1,
        player_input="test_input"
    )
    
    # Mock workflow result with decision without next_section
    mock_decision = DecisionModel(
        section_number=1,
        next_section=None,
    )
    mock_result = {
        "decision": mock_decision
    }
    
    # Setup mock workflow manager
    mock_managers['workflow_manager'].execute_workflow.return_value = mock_result
    
    # Execute test
    new_state = await agent_manager.process_game_state(initial_state)
    
    # Verify state did not change
    assert new_state == initial_state
    
    # Verify state was not saved
    mock_managers['state_manager'].save_state.assert_not_called()

@pytest.mark.asyncio
async def test_state_transition_with_invalid_next_section(agent_manager, mock_managers):
    """Test that state transition fails with invalid next_section."""
    # Initial state
    initial_state = GameState(
        session_id="test_session",
        game_id="test_game",
        section_number=1,
        player_input="test_input"
    )
    
    # Mock workflow result with invalid next_section
    mock_decision = DecisionModel(
        section_number=1,
        next_section=-1,  # Invalid section number
    )
    mock_result = {
        "decision": mock_decision
    }
    
    # Setup mock workflow manager
    mock_managers['workflow_manager'].execute_workflow.return_value = mock_result
    
    # Execute test and verify it raises an error
    with pytest.raises(StateError):
        await agent_manager.process_game_state(initial_state)
    
    # Verify state was not saved
    mock_managers['state_manager'].save_state.assert_not_called()
