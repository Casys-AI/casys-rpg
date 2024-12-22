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

@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager."""
    cache = Mock()
    cache.get_cached_content = AsyncMock()
    cache.save_cached_content = AsyncMock()
    cache.load_raw_content = AsyncMock()
    return cache

@pytest.fixture
def config():
    """Create a test storage config."""
    return StorageConfig.get_default_config(base_path="./test_data")

@pytest_asyncio.fixture
async def narrator_manager(config, mock_cache_manager):
    """Create a test narrator manager."""
    manager = NarratorManager(config=config, cache_manager=mock_cache_manager)
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
