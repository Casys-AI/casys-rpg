"""Tests for the narrator agent module."""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime

from agents.narrator_agent import NarratorAgent
from config.agents.narrator_agent_config import NarratorAgentConfig
from models.narrator_model import NarratorModel, SourceType
from models.errors_model import NarratorError

@pytest.fixture
def mock_narrator_manager():
    """Create a mock narrator manager."""
    manager = Mock()
    manager.get_section_content = AsyncMock()
    manager.get_raw_section_content = AsyncMock()
    manager.save_section_content = AsyncMock()
    return manager

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.ainvoke = AsyncMock()
    return llm

@pytest.fixture
def config(mock_llm):
    """Create a test narrator agent config."""
    return NarratorAgentConfig(
        llm=mock_llm,
        system_message="Test system message"
    )

@pytest_asyncio.fixture
async def narrator_agent(config, mock_narrator_manager):
    """Create a test narrator agent."""
    agent = NarratorAgent(config=config, narrator_manager=mock_narrator_manager)
    return agent

@pytest.fixture
def sample_markdown_content():
    """Sample markdown content for testing."""
    return """# Section 1

This is a test section.
- Point 1
- Point 2

## Subsection
More content here."""

@pytest.fixture
def sample_narrator_model():
    """Create a sample narrator model."""
    return NarratorModel(
        section_number=1,
        content="""This is a test section.
- Point 1
- Point 2

## Subsection
More content here.""",
        source_type=SourceType.PROCESSED,
        timestamp=datetime.now()
    )

@pytest.mark.asyncio
async def test_process_section_cache_hit(narrator_agent, mock_narrator_manager, sample_narrator_model):
    """Test processing a section with cache hit."""
    # Setup mock
    mock_narrator_manager.get_section_content.return_value = sample_narrator_model
    
    # Process section
    result = await narrator_agent.process_section(1)
    
    # Verify result
    assert isinstance(result, NarratorModel)
    assert result.section_number == 1
    assert result.content == sample_narrator_model.content
    assert result.source_type == SourceType.PROCESSED
    
    # Verify manager calls
    mock_narrator_manager.get_section_content.assert_called_once_with(1)
    mock_narrator_manager.get_raw_section_content.assert_not_called()

@pytest.mark.asyncio
async def test_process_section_cache_miss(
    narrator_agent, mock_narrator_manager, mock_llm, sample_markdown_content
):
    """Test processing a section with cache miss."""
    # Setup mocks
    mock_narrator_manager.get_section_content.return_value = None
    mock_narrator_manager.get_raw_section_content.return_value = sample_markdown_content
    mock_llm.ainvoke.return_value.content = sample_markdown_content
    
    # Process section
    result = await narrator_agent.process_section(1)
    
    # Verify result
    assert isinstance(result, NarratorModel)
    assert result.section_number == 1
    assert result.source_type == SourceType.PROCESSED
    
    # Verify manager calls
    mock_narrator_manager.get_section_content.assert_called_once_with(1)
    mock_narrator_manager.get_raw_section_content.assert_called_once_with(1)
    mock_narrator_manager.save_section_content.assert_called_once()

@pytest.mark.asyncio
async def test_process_section_not_found(narrator_agent, mock_narrator_manager):
    """Test processing a non-existent section."""
    # Setup mock
    mock_narrator_manager.get_section_content.return_value = None
    mock_narrator_manager.get_raw_section_content.return_value = None
    
    # Process section
    result = await narrator_agent.process_section(999)
    
    # Verify result
    assert isinstance(result, NarratorError)
    assert result.section_number == 999
    assert "not found" in result.message.lower()

@pytest.mark.asyncio
async def test_process_section_with_error(narrator_agent, mock_narrator_manager, mock_llm):
    """Test processing a section with LLM error."""
    # Setup mocks
    mock_narrator_manager.get_section_content.return_value = None
    mock_narrator_manager.get_raw_section_content.return_value = "Test content"
    mock_llm.ainvoke.side_effect = Exception("LLM error")
    
    # Process section
    result = await narrator_agent.process_section(1)
    
    # Verify result
    assert isinstance(result, NarratorError)
    assert result.section_number == 1
    assert "llm error" in result.message.lower()

@pytest.mark.asyncio
async def test_process_section_with_raw_content(
    narrator_agent, mock_narrator_manager, mock_llm, sample_markdown_content
):
    """Test processing a section with provided raw content."""
    # Setup mock
    mock_llm.ainvoke.return_value.content = sample_markdown_content
    
    # Process section with raw content
    result = await narrator_agent.process_section(1, raw_content="Test raw content")
    
    # Verify result
    assert isinstance(result, NarratorModel)
    assert result.section_number == 1
    assert result.source_type == SourceType.PROCESSED
    
    # Verify manager calls
    mock_narrator_manager.get_section_content.assert_not_called()
    mock_narrator_manager.get_raw_section_content.assert_not_called()
    mock_narrator_manager.save_section_content.assert_called_once()
