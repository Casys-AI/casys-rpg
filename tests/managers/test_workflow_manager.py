"""Test workflow manager session handling."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
import os
import shutil

from managers.workflow_manager import WorkflowManager
from models.game_state import GameStateInput, GameState
from managers.protocols.state_manager_protocol import StateManagerProtocol
from managers.protocols.rules_manager_protocol import RulesManagerProtocol
from managers.state_manager import StateManager
from managers.cache_manager import CacheManager
from config.storage_config import StorageConfig

@pytest.fixture
def state_manager():
    manager = AsyncMock(spec=StateManagerProtocol)
    manager.get_game_id = AsyncMock(return_value=None)
    manager.initialize = AsyncMock()
    manager.create_initial_state = AsyncMock(return_value=GameState(section_number=1))
    return manager

@pytest.fixture
def rules_manager():
    return AsyncMock(spec=RulesManagerProtocol)

@pytest.fixture
def workflow_manager(state_manager, rules_manager):
    return WorkflowManager(state_manager, rules_manager)

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    yield data_dir
    # Cleanup
    shutil.rmtree(data_dir)

@pytest.mark.asyncio
async def test_start_workflow_new_session():
    """Test starting workflow with no existing game_id."""
    # Setup
    state_manager = AsyncMock(spec=StateManagerProtocol)
    state_manager.get_game_id.return_value = None
    workflow_manager = WorkflowManager(state_manager, AsyncMock(spec=RulesManagerProtocol))
    
    # Execute
    input_data = GameStateInput()
    result = await workflow_manager.start_workflow(input_data)
    
    # Assert
    assert result.state is not None
    assert state_manager.initialize.call_count == 1
    # Le game_id utilisé pour initialize doit être le même que celui utilisé pour create_initial_state
    game_id = state_manager.initialize.call_args[0][0]
    assert state_manager.create_initial_state.call_args[1]["session_id"] == game_id

@pytest.mark.asyncio
async def test_start_workflow_existing_session():
    """Test starting workflow with existing game_id."""
    # Setup
    state_manager = AsyncMock(spec=StateManagerProtocol)
    existing_id = "existing-game-id"
    state_manager.get_game_id.return_value = existing_id
    workflow_manager = WorkflowManager(state_manager, AsyncMock(spec=RulesManagerProtocol))
    
    # Execute
    input_data = GameStateInput()
    result = await workflow_manager.start_workflow(input_data)
    
    # Assert
    assert result.state is not None
    assert state_manager.initialize.call_count == 0  # Ne devrait pas être appelé
    assert state_manager.create_initial_state.call_args[1]["session_id"] == existing_id

@pytest.mark.asyncio
async def test_cache_directory_creation(temp_data_dir):
    """Test that cache directories are created with correct game_id."""
    # Setup
    config = StorageConfig(base_path=temp_data_dir)
    cache_manager = CacheManager(config)
    state_manager = StateManager(config, cache_manager)
    rules_manager = AsyncMock(spec=RulesManagerProtocol)
    workflow_manager = WorkflowManager(state_manager, rules_manager)
    
    # Execute
    input_data = GameStateInput()
    result = await workflow_manager.start_workflow(input_data)
    
    # Get game_id from state manager
    game_id = await state_manager.get_game_id()
    
    # Assert
    # Vérifie que le dossier de cache existe
    cache_dir = temp_data_dir / "cache" / "games" / game_id / "states"
    assert cache_dir.exists(), f"Cache directory not created: {cache_dir}"
    
    # Vérifie que le dossier contient des fichiers d'état
    state_files = list(cache_dir.glob("*.json"))
    assert len(state_files) > 0, "No state files created in cache directory"
