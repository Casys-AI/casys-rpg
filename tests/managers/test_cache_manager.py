"""Tests for the cache manager module."""
import pytest
import pytest_asyncio
from unittest.mock import Mock, patch
from datetime import datetime
from pathlib import Path

from managers.cache_manager import CacheManager, CacheEntry
from config.storage_config import StorageConfig, StorageFormat
from models.trace_model import TraceModel

@pytest.fixture
def config():
    """Create a test storage config."""
    return StorageConfig.get_default_config(base_path="./test_data")

@pytest.fixture
def cache_manager(config):
    """Create a test cache manager."""
    manager = CacheManager(config=config)
    return manager

@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return {
        "key": "value",
        "number": 42,
        "timestamp": datetime.now().isoformat()
    }

@pytest.fixture
def sample_model():
    """Sample pydantic model for testing."""
    return TraceModel(
        session_id="test-session",
        start_time=datetime.now(),
        history=[]
    )

def test_cache_entry():
    """Test CacheEntry functionality."""
    # Test without TTL
    entry = CacheEntry(value="test", ttl_seconds=None)
    assert entry.value == "test"
    assert entry.expiry is None
    assert not entry.is_expired()
    
    # Test with TTL
    entry = CacheEntry(value="test", ttl_seconds=3600)
    assert entry.value == "test"
    assert entry.expiry is not None
    assert not entry.is_expired()

def test_get_cache_key(cache_manager):
    """Test cache key generation."""
    key = cache_manager._get_cache_key("test-key", "test-namespace")
    assert key == "test-namespace:test-key"

def test_get_file_extension(cache_manager):
    """Test file extension retrieval."""
    # JSON format
    ext = cache_manager._get_file_extension("state")
    assert ext == ".json"
    
    # Markdown format
    ext = cache_manager._get_file_extension("sections")
    assert ext == ".md"

@pytest.mark.asyncio
async def test_save_cached_content(cache_manager, sample_data):
    """Test saving content to cache."""
    # Save JSON data
    await cache_manager.save_cached_content(
        key="test",
        namespace="state",
        data=sample_data
    )
    
    # Verify it's in memory cache
    cache_key = cache_manager._get_cache_key("test", "state")
    assert cache_key in cache_manager._memory_cache
    assert cache_manager._memory_cache[cache_key].value == sample_data

@pytest.mark.asyncio
async def test_get_cached_content(cache_manager, sample_data):
    """Test retrieving cached content."""
    # Save data first
    await cache_manager.save_cached_content(
        key="test",
        namespace="state",
        data=sample_data
    )
    
    # Get from cache
    result = await cache_manager.get_cached_content(
        key="test",
        namespace="state"
    )
    assert result == sample_data
    
    # Get non-existent key
    result = await cache_manager.get_cached_content(
        key="non-existent",
        namespace="state"
    )
    assert result is None

@pytest.mark.asyncio
async def test_model_serialization(cache_manager, sample_model):
    """Test model serialization/deserialization."""
    # Save model
    await cache_manager.save_cached_content(
        key="test-model",
        namespace="trace",
        data=sample_model
    )
    
    # Get model back
    result = await cache_manager.get_cached_content(
        key="test-model",
        namespace="trace"
    )
    assert isinstance(result, dict)  # Should be deserialized to dict
    assert result["session_id"] == sample_model.session_id
