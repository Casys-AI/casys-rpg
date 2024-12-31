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
def mock_config():
    """Create a mock configuration."""
    return StorageConfig(base_path=Path("./test_data"))

@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager."""
    cache = AsyncMock()
    cache.get_cached_data = AsyncMock(return_value=None)
    cache.save_cached_data = AsyncMock()
    cache.exists_data = AsyncMock(return_value=True)
    cache.exists_raw_content = AsyncMock(return_value=True)
    cache.load_raw_content = AsyncMock(return_value=None)
    return cache

@pytest.fixture
def narrator_manager(mock_config, mock_cache_manager):
    """Create a test narrator manager."""
    return NarratorManager(
        config=mock_config,
        cache_manager=mock_cache_manager
    )

@pytest.fixture
def sample_content():
    """Sample content for testing."""
    return {
        "section_number": 1,
        "content": "Test content",
        "source_type": SourceType.RAW
    }

@pytest.fixture
def sample_narrator_model():
    """Create a sample narrator model."""
    return NarratorModel(
        section_number=1,
        content="Test content",
        source_type=SourceType.PROCESSED,
        timestamp=datetime.now()
    )

@pytest.mark.asyncio
async def test_get_cached_content(narrator_manager, mock_cache_manager, sample_narrator_model):
    """Test getting cached content."""
    # Setup mock with markdown format
    mock_cache_manager.get_cached_data.return_value = f"# Section {sample_narrator_model.section_number}\n{sample_narrator_model.content}"

    # Test getting existing content
    result = await narrator_manager.get_cached_content(1)
    assert result is not None
    assert result.section_number == sample_narrator_model.section_number
    assert result.content == sample_narrator_model.content
    mock_cache_manager.get_cached_data.assert_called_once_with(
        key="section_1",
        namespace="sections"
    )

    # Test getting non-existent content
    mock_cache_manager.get_cached_data.return_value = None
    result = await narrator_manager.get_cached_content(2)
    assert result is None

@pytest.mark.asyncio
async def test_save_content(narrator_manager, mock_cache_manager, sample_narrator_model):
    """Test saving content."""
    await narrator_manager.save_content(sample_narrator_model)
    mock_cache_manager.save_cached_data.assert_called_once_with(
        key=f"section_{sample_narrator_model.section_number}",
        data=sample_narrator_model.content.strip(),
        namespace="sections"
    )

@pytest.mark.asyncio
async def test_exists_section(narrator_manager, mock_cache_manager):
    """Test checking if section exists."""
    # Test existing section
    mock_cache_manager.exists_data.return_value = True
    result = await narrator_manager.exists_section(1)
    assert result is True
    mock_cache_manager.exists_data.assert_called_with(
        key="section_1",
        namespace="sections"
    )

    # Test non-existent section
    mock_cache_manager.exists_data.return_value = False
    result = await narrator_manager.exists_section(2)
    assert result is False

@pytest.mark.asyncio
async def test_load_raw_content(narrator_manager, mock_cache_manager, sample_content):
    """Test loading raw content."""
    # Test successful load
    mock_cache_manager.load_raw_content.return_value = sample_content
    result = await narrator_manager.load_raw_content(1)
    assert result == sample_content
    mock_cache_manager.load_raw_content.assert_called_with(
        key="1",
        namespace="raw_content"
    )

    # Test load with error
    mock_cache_manager.load_raw_content.side_effect = Exception("Test error")
    with pytest.raises(NarratorError):
        await narrator_manager.load_raw_content(1)
