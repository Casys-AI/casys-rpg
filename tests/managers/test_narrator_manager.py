"""Tests for the narrator manager module."""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from pathlib import Path

from managers.narrator_manager import NarratorManager
from config.storage_config import StorageConfig
from models.narrator_model import NarratorModel, SourceType
from models.errors_model import NarratorError
from utils.markdown_formatter import MarkdownFormatter

@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager."""
    cache = AsyncMock()
    cache.get_cached_content = AsyncMock(return_value=None)
    cache.load_raw_content = AsyncMock(return_value=None)
    cache.save_cached_content = AsyncMock()
    cache.exists_raw_content = AsyncMock(return_value=True)
    return cache

@pytest.fixture
def mock_config():
    """Create a test storage config."""
    return StorageConfig(base_path="/test/path")

@pytest.fixture
def narrator_manager(mock_config, mock_cache_manager):
    """Create a test narrator manager."""
    manager = NarratorManager(config=mock_config, cache_manager=mock_cache_manager)
    return manager

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
        source_type=SourceType.RAW,
        timestamp=datetime.now()
    )

@pytest.fixture
def sample_content():
    """Sample content for testing."""
    return """# Section 1
    
This is a test section with some content."""

@pytest.fixture
def sample_model():
    """Create a sample narrator model."""
    return NarratorModel(
        section_number=1,
        content="# Section 1\nTest content",
        source_type=SourceType.PROCESSED,
        timestamp=datetime.now()
    )

@pytest.mark.asyncio
async def test_get_raw_section_content(narrator_manager, mock_cache_manager, sample_markdown_content):
    """Test getting raw section content."""
    # Configure mock
    mock_cache_manager.load_raw_content.return_value = sample_markdown_content
    
    # Test successful retrieval
    content = await narrator_manager.get_raw_section_content(1)
    assert content == sample_markdown_content
    mock_cache_manager.load_raw_content.assert_called_once_with(
        section_number=1,
        namespace="sections"
    )
    
    # Test non-existent section
    mock_cache_manager.load_raw_content.return_value = None
    content = await narrator_manager.get_raw_section_content(999)
    assert content is None

@pytest.mark.asyncio
async def test_get_section_content(narrator_manager, mock_cache_manager, sample_markdown_content, sample_narrator_model):
    """Test getting processed section content."""
    # Test cache hit
    mock_cache_manager.get_cached_content.return_value = sample_markdown_content
    result = await narrator_manager.get_section_content(1)
    assert isinstance(result, NarratorModel)
    assert result.section_number == 1
    assert result.content == sample_markdown_content
    
    # Test cache miss but raw content exists
    mock_cache_manager.get_cached_content.return_value = None
    mock_cache_manager.load_raw_content.return_value = sample_markdown_content
    result = await narrator_manager.get_section_content(1)
    assert isinstance(result, NarratorModel)
    assert result.section_number == 1
    assert result.source_type == SourceType.PROCESSED
    
    # Test section not found
    mock_cache_manager.get_cached_content.return_value = None
    mock_cache_manager.load_raw_content.return_value = None
    result = await narrator_manager.get_section_content(999)
    assert isinstance(result, NarratorError)
    assert result.section_number == 999

@pytest.mark.asyncio
async def test_save_section_content(narrator_manager, mock_cache_manager, sample_narrator_model):
    """Test saving section content."""
    # Test successful save
    mock_cache_manager.save_cached_content.return_value = True
    result = await narrator_manager.save_section_content(sample_narrator_model)
    assert result is None  # No error returned means success
    mock_cache_manager.save_cached_content.assert_called_once()
    
    # Test save failure
    mock_cache_manager.save_cached_content.return_value = False
    result = await narrator_manager.save_section_content(sample_narrator_model)
    assert isinstance(result, NarratorError)

@pytest.mark.asyncio
async def test_markdown_conversion(narrator_manager, sample_narrator_model, sample_markdown_content):
    """Test markdown conversion methods."""
    # Test markdown to content
    content_model = narrator_manager._markdown_to_content(sample_markdown_content, 1)
    assert isinstance(content_model, NarratorModel)
    assert content_model.section_number == 1
    assert content_model.content == sample_markdown_content
    
    # Test content to markdown
    markdown = narrator_manager._content_to_markdown(sample_narrator_model)
    assert isinstance(markdown, str)
    assert markdown == sample_narrator_model.content

@pytest.mark.asyncio
async def test_error_handling(narrator_manager, mock_cache_manager, sample_narrator_model):
    """Test error handling."""
    # Test exception in get_cached_content
    mock_cache_manager.get_cached_content.side_effect = Exception("Cache error")
    result = await narrator_manager.get_section_content(1)
    assert isinstance(result, NarratorError)
    assert "Cache error" in result.message
    
    # Test exception in save_cached_content
    mock_cache_manager.save_cached_content.side_effect = Exception("Save error")
    result = await narrator_manager.save_section_content(sample_narrator_model)
    assert isinstance(result, NarratorError)
    assert "Save error" in result.message

@pytest.mark.asyncio
async def test_get_cached_content_hit(narrator_manager, mock_cache_manager, sample_content):
    """Test getting content from cache when it exists."""
    mock_cache_manager.get_cached_content.return_value = sample_content
    result = await narrator_manager.get_cached_content(1)
    assert isinstance(result, NarratorModel)
    assert result.section_number == 1
    assert "Section 1" in result.content

@pytest.mark.asyncio
async def test_get_cached_content_miss(narrator_manager, mock_cache_manager):
    """Test getting content from cache when it doesn't exist."""
    mock_cache_manager.get_cached_content.return_value = None
    result = await narrator_manager.get_cached_content(1)
    assert result is None

@pytest.mark.asyncio
async def test_get_raw_content_success(narrator_manager, mock_cache_manager, sample_content):
    """Test getting raw content successfully."""
    mock_cache_manager.load_raw_content.return_value = sample_content
    result = await narrator_manager.get_raw_content(1)
    assert isinstance(result, str)
    assert result == sample_content

@pytest.mark.asyncio
async def test_get_raw_content_not_found(narrator_manager, mock_cache_manager):
    """Test getting raw content when it doesn't exist."""
    mock_cache_manager.exists_raw_content.return_value = False
    result = await narrator_manager.get_raw_content(1)
    assert isinstance(result, NarratorError)
    assert "No raw content found" in result.message

@pytest.mark.asyncio
async def test_save_content_success(narrator_manager, mock_cache_manager, sample_model):
    """Test saving content successfully."""
    result = await narrator_manager.save_content(sample_model)
    assert isinstance(result, NarratorModel)
    assert result.section_number == sample_model.section_number
    mock_cache_manager.save_cached_content.assert_called_once()

@pytest.mark.asyncio
async def test_save_content_error(narrator_manager, mock_cache_manager, sample_model):
    """Test saving content with error."""
    mock_cache_manager.save_cached_content.side_effect = Exception("Test error")
    result = await narrator_manager.save_content(sample_model)
    assert isinstance(result, NarratorError)
    assert "Error saving content" in result.message

def test_format_content_valid(narrator_manager, sample_content):
    """Test formatting valid content."""
    result = narrator_manager.format_content(sample_content, 1)
    assert isinstance(result, NarratorModel)
    assert result.section_number == 1
    assert result.content == sample_content

def test_format_content_invalid(narrator_manager):
    """Test formatting invalid content."""
    result = narrator_manager.format_content("Invalid content", 1)
    assert isinstance(result, NarratorError)
    assert "Invalid content format" in result.message

@pytest.mark.asyncio
async def test_exists_raw_section(narrator_manager, mock_cache_manager):
    """Test checking if raw section exists."""
    mock_cache_manager.exists_raw_content.return_value = True
    result = await narrator_manager.exists_raw_section(1)
    assert result is True
    mock_cache_manager.exists_raw_content.assert_called_once()
