"""Manager-specific test fixtures."""

import pytest
from unittest.mock import AsyncMock
from pathlib import Path

from config.storage_config import StorageConfig

@pytest.fixture
def base_config():
    """Create base configuration for tests."""
    return StorageConfig(base_path=Path("./test_data"))

@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager."""
    manager = AsyncMock()
    manager.get_cached_data = AsyncMock(return_value=None)
    manager.save_cached_data = AsyncMock()
    manager.exists_data = AsyncMock(return_value=True)
    manager.load_raw_data = AsyncMock(return_value=None)
    return manager

@pytest.fixture
def mock_state_manager():
    """Create a mock state manager."""
    manager = AsyncMock()
    manager.get_current_state = AsyncMock()
    manager.update_state = AsyncMock()
    return manager

@pytest.fixture
def mock_managers(mock_cache_manager, mock_state_manager):
    """Create all mock managers."""
    return {
        "cache_manager": mock_cache_manager,
        "state_manager": mock_state_manager
    }
