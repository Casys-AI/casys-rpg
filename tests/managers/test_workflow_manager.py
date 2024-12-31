"""Test workflow manager session handling."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import os
import shutil
import uuid

from managers.protocols.workflow_manager_protocol import WorkflowManagerProtocol
from models.game_state import GameStateInput, GameState
from managers.protocols.state_manager_protocol import StateManagerProtocol
from managers.protocols.rules_manager_protocol import RulesManagerProtocol
from managers.workflow_manager import WorkflowManager
from managers.state_manager import StateManager
from managers.cache_manager import CacheManager
from config.storage_config import StorageConfig

@pytest.fixture
def state_manager():
    manager = AsyncMock(spec=StateManagerProtocol)
    manager.get_game_id = AsyncMock(return_value=None)
    manager.initialize = AsyncMock()
    test_session_id = str(uuid.uuid4())
    test_game_id = str(uuid.uuid4())
    manager.create_initial_state = AsyncMock(return_value=GameState(
        section_number=1,
        session_id=test_session_id,
        game_id=test_game_id
    ))
    return manager

@pytest.fixture
def rules_manager():
    return AsyncMock(spec=RulesManagerProtocol)

@pytest.fixture
def workflow_manager(state_manager, rules_manager):
    return WorkflowManager(state_manager, rules_manager)

@pytest.mark.asyncio
async def test_start_workflow_new_session(workflow_manager, state_manager):
    """Test starting workflow with no existing game_id."""
    # Setup
    state_manager.get_game_id.return_value = None
    test_session_id = str(uuid.uuid4())
    test_game_id = str(uuid.uuid4())
    test_input = {"some": "data"}
    
    # Test
    await workflow_manager.start_workflow(test_input)
    
    # Verify
    state_manager.initialize.assert_called_once()
    state_manager.create_initial_state.assert_called_once()

@pytest.mark.asyncio
async def test_start_workflow_existing_session(workflow_manager, state_manager):
    """Test starting workflow with existing game_id."""
    # Setup
    existing_game_id = str(uuid.uuid4())
    state_manager.get_game_id.return_value = existing_game_id
    
    # Test
    await workflow_manager.start_workflow()
    
    # Verify
    state_manager.initialize.assert_not_called()
    state_manager.create_initial_state.assert_not_called()

@pytest.mark.asyncio
async def test_cache_directory_creation(temp_data_dir, workflow_manager, state_manager):
    """Test that cache directories are created with correct game_id."""
    # Setup
    game_id = str(uuid.uuid4())
    state_manager.get_game_id.return_value = game_id
    cache_dir = temp_data_dir / game_id
    
    # Test
    await workflow_manager.start_workflow()
    
    # Verify
    assert cache_dir.exists()
    assert cache_dir.is_dir()
    
    # Cleanup
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
