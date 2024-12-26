"""Tests for the narrator manager module."""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from managers.narrator_manager import NarratorManager
from config.storage_config import StorageConfig
from models.narrator_model import NarratorModel, SourceType
from models.errors_model import NarratorError

@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager."""
    cache = AsyncMock()
    cache.get_cached_data = AsyncMock(return_value=None)
    cache.save_cached_data = AsyncMock()
    cache.exists_data = AsyncMock(return_value=True)
    cache.load_raw_data = AsyncMock(return_value=None)
    return cache

@pytest.fixture
def mock_config():
    """Create a test storage config."""
    return StorageConfig(base_path="/test/path")

@pytest.fixture
def narrator_manager(mock_config, mock_cache_manager):
    """Create a test narrator manager."""
    return NarratorManager(config=mock_config, cache_manager=mock_cache_manager)

@pytest.fixture
def sample_content():
    """Sample content for testing."""
    return """# Section 1
    
This is a test section with some content."""

@pytest.fixture
def sample_narrator_model():
    """Create a sample narrator model."""
    return NarratorModel(
        section_number=1,
        content="# Section 1\nTest content",
        source_type=SourceType.PROCESSED,
        timestamp=datetime.now()
    )

@pytest.mark.asyncio
async def test_get_cached_content(narrator_manager, mock_cache_manager, sample_narrator_model):
    """Test getting cached content."""
    # Configure mock
    mock_cache_manager.get_cached_data.return_value = sample_narrator_model.model_dump()
    
    # Test successful retrieval
    content = await narrator_manager.get_cached_content(1)
    assert content is not None
    assert content.section_number == sample_narrator_model.section_number
    mock_cache_manager.get_cached_data.assert_called_once_with(
        key="section_1",
        namespace="sections"
    )
    
    # Test cache miss
    mock_cache_manager.get_cached_data.return_value = None
    content = await narrator_manager.get_cached_content(999)
    assert content is None

@pytest.mark.asyncio
async def test_save_content(narrator_manager, mock_cache_manager, sample_narrator_model):
    """Test saving content."""
    # Test successful save
    await narrator_manager.save_content(sample_narrator_model)
    mock_cache_manager.save_cached_data.assert_called_once_with(
        key=f"section_{sample_narrator_model.section_number}",
        data=sample_narrator_model.model_dump(),
        namespace="sections"
    )

@pytest.mark.asyncio
async def test_exists_section(narrator_manager, mock_cache_manager):
    """Test checking if section exists."""
    # Test existing section
    mock_cache_manager.exists_data.return_value = True
    exists = await narrator_manager.exists_section(1)
    assert exists is True
    mock_cache_manager.exists_data.assert_called_with(
        key="section_1",
        namespace="sections"
    )
    
    # Test non-existent section
    mock_cache_manager.exists_data.return_value = False
    exists = await narrator_manager.exists_section(999)
    assert exists is False

@pytest.mark.asyncio
async def test_load_raw_content(narrator_manager, mock_cache_manager, sample_content):
    """Test loading raw content."""
    # Test successful load
    mock_cache_manager.load_raw_data.return_value = sample_content
    content = await narrator_manager.load_raw_content(1)
    assert content == sample_content
    mock_cache_manager.load_raw_data.assert_called_with(
        key="section_1",
        namespace="sections"
    )
    
    # Test failed load
    mock_cache_manager.load_raw_data.return_value = None
    content = await narrator_manager.load_raw_content(999)
    assert content is None
