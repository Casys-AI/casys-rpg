"""Tests for StoryGraph agent."""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Any, AsyncIterator

from models.game_state import GameStateInput, GameStateOutput
from models.rules_model import RulesModel
from models.narrator_model import NarratorModel
from config.agents.agent_config_base import AgentConfigBase

class MockStoryGraph:
    """Mock story graph for testing."""
    
    def __init__(self):
        """Initialize with basic mocks."""
        self.rules_agent = AsyncMock()
        self.narrator_agent = AsyncMock()
        self.decision_agent = AsyncMock()
        self.trace_agent = AsyncMock()
        
        # Configure default returns
        self.rules_agent.process_rules = AsyncMock(return_value=RulesModel(section_number=1))
        self.narrator_agent.generate_narrative = AsyncMock(return_value=NarratorModel(section_number=1))

@pytest_asyncio.fixture
async def mock_story_graph():
    """Create a mock story graph."""
    return MockStoryGraph()

@pytest.mark.asyncio
async def test_process_rules(mock_story_graph):
    """Test rules processing."""
    # Arrange
    input_state = GameStateInput(
        session_id="test_session",
        game_id="test_game",
        section_number=1
    )
    
    # Act
    rules_model = await mock_story_graph.rules_agent.process_rules(input_state)
    
    # Assert
    assert rules_model.section_number == 1
    mock_story_graph.rules_agent.process_rules.assert_called_once_with(input_state)

@pytest.mark.asyncio
async def test_process_narrative(mock_story_graph):
    """Test narrative processing."""
    # Arrange
    input_state = GameStateInput(
        session_id="test_session",
        game_id="test_game",
        section_number=1
    )
    
    # Act
    narrative_model = await mock_story_graph.narrator_agent.generate_narrative(input_state)
    
    # Assert
    assert narrative_model.section_number == 1
    mock_story_graph.narrator_agent.generate_narrative.assert_called_once_with(input_state)

@pytest.mark.asyncio
async def test_parallel_processing(mock_story_graph):
    """Test parallel processing of rules and narrative."""
    # Arrange
    input_state = GameStateInput(
        session_id="test_session",
        game_id="test_game",
        section_number=1
    )
    
    # Act
    rules_model = await mock_story_graph.rules_agent.process_rules(input_state)
    narrative_model = await mock_story_graph.narrator_agent.generate_narrative(input_state)
    
    # Assert
    assert rules_model.section_number == narrative_model.section_number
    mock_story_graph.rules_agent.process_rules.assert_called_once()
    mock_story_graph.narrator_agent.generate_narrative.assert_called_once()
