"""Tests for StoryGraph agent."""
import pytest
from unittest.mock import AsyncMock
from typing import Any, AsyncIterator

from models.game_state import GameStateInput, GameStateOutput
from models.rules_model import RulesModel
from models.narrator_model import NarratorModel
from models.types.agent_types import GameAgents
from models.types.manager_types import GameManagers
from config.agents.agent_config_base import AgentConfigBase
from agents.story_graph import StoryGraph

@pytest.fixture
def mock_managers():
    """Create mock managers."""
    managers = GameManagers(
        state_manager=AsyncMock(),
        workflow_manager=AsyncMock(),
        rules_manager=AsyncMock(),
        narrator_manager=AsyncMock(),
        decision_manager=AsyncMock(),
        trace_manager=AsyncMock(),
        cache_manager=AsyncMock(),
        character_manager=AsyncMock()
    )
    return managers

@pytest.fixture
def mock_agents():
    """Create mock agents."""
    agents = GameAgents(
        rules_agent=AsyncMock(),
        narrator_agent=AsyncMock(),
        decision_agent=AsyncMock(),
        trace_agent=AsyncMock()
    )
    # Configure default returns
    agents.rules_agent.process_rules = AsyncMock(return_value=RulesModel())
    agents.narrator_agent.generate_narrative = AsyncMock(return_value=NarratorModel())
    return agents

@pytest.fixture
def story_graph(mock_managers, mock_agents):
    """Create StoryGraph instance with mocked dependencies."""
    config = AgentConfigBase()
    return StoryGraph(config=config, managers=mock_managers, agents=mock_agents)

@pytest.mark.asyncio
async def test_process_rules(story_graph, mock_agents):
    """Test _process_rules method."""
    # Setup
    input_state = GameStateInput(section_number=1, content="test content")
    mock_rules = RulesModel(section_number=1, content="test rules")
    mock_agents.rules_agent.process_rules.return_value = mock_rules

    # Execute
    result = await story_graph._process_rules(input_state)

    # Verify
    assert isinstance(result, GameStateOutput)
    assert result.rules == mock_rules
    assert result.section_number == input_state.section_number
    mock_agents.rules_agent.process_rules.assert_called_once_with(
        input_state.section_number,
        input_state.content
    )

@pytest.mark.asyncio
async def test_process_narrative(story_graph, mock_agents):
    """Test _process_narrative method."""
    # Setup
    input_state = GameStateInput(section_number=1, content="test content")
    mock_narrative = NarratorModel(section_number=1, content="test narrative")
    mock_agents.narrator_agent.generate_narrative.return_value = mock_narrative

    # Execute
    result = await story_graph._process_narrative(input_state)

    # Verify
    assert isinstance(result, GameStateOutput)
    assert result.narrative == mock_narrative
    assert result.section_number == input_state.section_number
    mock_agents.narrator_agent.generate_narrative.assert_called_once_with(
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
    
    mock_agents.rules_agent.process_rules.return_value = mock_rules
    mock_agents.narrator_agent.generate_narrative.return_value = mock_narrative

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
    mock_agents.rules_agent.process_rules.assert_called_once()
    mock_agents.narrator_agent.generate_narrative.assert_called_once()
