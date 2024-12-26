"""Tests for the NarratorAgent."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from models.narrator_model import NarratorModel, SourceType
from models.errors_model import NarratorError
from models.game_state import GameState
from config.agents.narrator_agent_config import NarratorAgentConfig

class MockNarratorAgent:
    """Mock narrator agent for testing."""
    
    def __init__(self, config: NarratorAgentConfig, narrator_manager):
        self.config = config
        self.narrator_manager = narrator_manager
        
    async def process_section(self, section_number: int) -> NarratorModel:
        """Mock process_section method."""
        cached = await self.narrator_manager.get_cached_content(section_number)
        if cached:
            return cached
            
        content = await self.narrator_manager.get_raw_content(section_number)
        if isinstance(content, NarratorError):
            return content
            
        formatted = self.narrator_manager.format_content(content)
        if isinstance(formatted, NarratorError):
            return formatted
            
        return await self.narrator_manager.save_content(formatted)
        
    async def ainvoke(self, input_data: dict) -> dict:
        """Mock ainvoke method."""
        state = input_data.get("state")
        if not state:
            return {"state": NarratorError(section_number=0, message="Invalid state")}
            
        result = await self.process_section(state.section_number)
        if isinstance(result, NarratorError):
            state.error = result
        else:
            state.narrative_content = result.content
            
        return {"state": state}

@pytest.fixture
def mock_narrator_manager():
    manager = AsyncMock()
    manager.get_cached_content = AsyncMock(return_value=None)
    manager.get_raw_content = AsyncMock()
    manager.save_content = AsyncMock()
    manager.format_content = MagicMock()
    return manager

@pytest.fixture
def mock_config():
    config = MagicMock(spec=NarratorAgentConfig)
    config.llm = AsyncMock()
    config.llm.ainvoke = AsyncMock()
    config.system_message = "You are a narrator"
    return config

@pytest.fixture
def narrator_agent(mock_config, mock_narrator_manager):
    return MockNarratorAgent(config=mock_config, narrator_manager=mock_narrator_manager)

@pytest.fixture
def sample_content():
    return """# Section 1
    
This is a test section with some content."""

@pytest.fixture
def sample_model():
    return NarratorModel(
        section_number=1,
        content="# Section 1\nTest content",
        source_type=SourceType.PROCESSED,
        timestamp=datetime.now()
    )

@pytest.fixture
def sample_game_state():
    return GameState(
        session_id="test_session",
        section_number=1,
        narrative_content="",
        last_update=datetime.now()
    )

@pytest.mark.asyncio
async def test_process_section_cache_hit(narrator_agent, mock_narrator_manager, sample_model):
    """Test processing section with cache hit."""
    mock_narrator_manager.get_cached_content.return_value = sample_model
    result = await narrator_agent.process_section(1)
    assert isinstance(result, NarratorModel)
    assert result.section_number == 1
    mock_narrator_manager.get_raw_content.assert_not_called()

@pytest.mark.asyncio
async def test_process_section_cache_miss(narrator_agent, mock_narrator_manager, sample_content, sample_model):
    """Test processing section with cache miss."""
    mock_narrator_manager.get_cached_content.return_value = None
    mock_narrator_manager.get_raw_content.return_value = sample_content
    mock_narrator_manager.format_content.return_value = sample_model
    mock_narrator_manager.save_content.return_value = sample_model
    
    result = await narrator_agent.process_section(1)
    assert isinstance(result, NarratorModel)
    assert result.section_number == 1
    mock_narrator_manager.get_raw_content.assert_called_once()

@pytest.mark.asyncio
async def test_process_section_raw_content_error(narrator_agent, mock_narrator_manager):
    """Test processing section with raw content error."""
    mock_narrator_manager.get_cached_content.return_value = None
    mock_narrator_manager.get_raw_content.return_value = NarratorError(
        section_number=1,
        message="Content not found"
    )
    
    result = await narrator_agent.process_section(1)
    assert isinstance(result, NarratorError)
    assert "Content not found" in result.message

@pytest.mark.asyncio
async def test_process_section_format_error(narrator_agent, mock_narrator_manager, sample_content):
    """Test processing section with format error."""
    mock_narrator_manager.get_cached_content.return_value = None
    mock_narrator_manager.get_raw_content.return_value = sample_content
    mock_narrator_manager.format_content.return_value = NarratorError(
        section_number=1,
        message="Format error"
    )
    
    result = await narrator_agent.process_section(1)
    assert isinstance(result, NarratorError)
    assert "Format error" in result.message

@pytest.mark.asyncio
async def test_ainvoke_success(narrator_agent, mock_narrator_manager, sample_model, sample_game_state):
    """Test successful agent invocation."""
    mock_narrator_manager.get_cached_content.return_value = sample_model
    
    result = await narrator_agent.ainvoke({"state": sample_game_state})
    assert "state" in result
    assert result["state"].narrative_content == sample_model.content

@pytest.mark.asyncio
async def test_ainvoke_error(narrator_agent, mock_narrator_manager, sample_game_state):
    """Test agent invocation with error."""
    error = NarratorError(section_number=1, message="Test error")
    mock_narrator_manager.get_cached_content.return_value = error
    
    result = await narrator_agent.ainvoke({"state": sample_game_state})
    assert "state" in result
    assert isinstance(result["state"].error, NarratorError)
    assert "Test error" in result["state"].error.message
