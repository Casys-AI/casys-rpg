"""Tests for StoryGraph agent."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from loguru import logger

from agents.story_graph import StoryGraph
from models.game_state import GameStateInput, GameStateOutput
from models.rules_model import RulesModel
from models.narrator_model import NarratorModel
from config.agents.agent_config_base import AgentConfigBase
from agents.factories.game_factory import GameAgents, GameManagers


@pytest.fixture
def mock_managers():
    """Create mock managers."""
    managers = MagicMock(spec=GameManagers)
    managers.state_manager = AsyncMock()
    managers.workflow_manager = AsyncMock()
    managers.rules_manager = AsyncMock()
    managers.narrator_manager = AsyncMock()
    managers.decision_manager = AsyncMock()
    managers.trace_manager = AsyncMock()
    return managers

@pytest.fixture
def mock_agents():
    """Create mock agents."""
    agents = MagicMock(spec=GameAgents)
    agents.rules_agent = AsyncMock()
    agents.narrator_agent = AsyncMock()
    agents.decision_agent = AsyncMock()
    agents.trace_agent = AsyncMock()
    return agents

@pytest.fixture
def story_graph(mock_managers, mock_agents):
    """Create StoryGraph instance with mocked dependencies."""
    config = AgentConfigBase()
    return StoryGraph(config, mock_managers, mock_agents)

@pytest.mark.asyncio
async def test_process_rules(story_graph, mock_agents):
    """Test _process_rules method."""
    # Setup
    input_state = GameStateInput(section_number=1, content="test content")
    mock_rules = RulesModel(section_number=1, content="test rules")
    mock_agents.rules_agent.process_section_rules.return_value = mock_rules

    # Execute
    result = await story_graph._process_rules(input_state)

    # Verify
    assert isinstance(result, GameStateOutput)
    assert result.rules == mock_rules
    assert result.section_number == input_state.section_number
    mock_agents.rules_agent.process_section_rules.assert_called_once_with(
        input_state.section_number,
        input_state.content
    )

@pytest.mark.asyncio
async def test_process_narrative(story_graph, mock_agents):
    """Test _process_narrative method."""
    # Setup
    input_state = GameStateInput(section_number=1, content="test content")
    mock_narrative = NarratorModel(section_number=1, content="test narrative")
    mock_agents.narrator_agent.process_section.return_value = mock_narrative

    # Execute
    result = await story_graph._process_narrative(input_state)

    # Verify
    assert isinstance(result, GameStateOutput)
    assert result.narrative == mock_narrative
    assert result.section_number == input_state.section_number
    mock_agents.narrator_agent.process_section.assert_called_once_with(
        input_state.section_number,
        input_state.content
    )

@pytest.mark.asyncio
async def test_parallel_processing(story_graph, mock_agents):
    """Test parallel processing workflow."""
    # Setup
    input_state = GameStateInput(section_number=1, content="test content")
    mock_rules = RulesModel(section_number=1, content="test rules")
    mock_narrative = NarratorModel(section_number=1, content="test narrative")
    
    mock_agents.rules_agent.process_section_rules.return_value = mock_rules
    mock_agents.narrator_agent.process_section.return_value = mock_narrative

    # Execute rules branch
    rules_result = await story_graph._process_rules(input_state)
    
    # Execute narrative branch
    narrative_result = await story_graph._process_narrative(input_state)

    # Verify rules branch
    assert isinstance(rules_result, GameStateOutput)
    assert rules_result.rules == mock_rules
    assert rules_result.narrative is None  # No narrative yet

    # Verify narrative branch
    assert isinstance(narrative_result, GameStateOutput)
    assert narrative_result.narrative == mock_narrative
    assert narrative_result.rules is None  # No rules yet

    # Verify parallel execution
    mock_agents.rules_agent.process_section_rules.assert_called_once()
    mock_agents.narrator_agent.process_section.assert_called_once()
