"""Test session_id handling in workflow."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from models.game_state import GameState
from managers.workflow_manager import WorkflowManager
from managers.state_manager import StateManager
from config.storage_config import StorageConfig
from models.character_model import CharacterModel, CharacterStats

@pytest.mark.asyncio
async def test_session_id_workflow():
    """Test session_id preservation through the workflow."""
    # Setup
    cache_manager = AsyncMock()
    cache_manager.save_cached_data = AsyncMock(return_value=True)
    
    state_manager = StateManager(
        config=StorageConfig(base_path="test_storage"),
        cache_manager=cache_manager
    )
    
    # 1. Create initial state
    initial_state = await state_manager.create_initial_state()
    print(f"\nInitial state created with session_id: {initial_state.session_id}")
    assert initial_state.session_id is not None, "Initial state should have session_id"
    original_session_id = initial_state.session_id
    
    # 2. Test with_updates preservation
    updated_state = initial_state.with_updates(
        player_input="test input",
        section_number=2
    )
    print(f"Updated state session_id: {updated_state.session_id}")
    assert updated_state.session_id == original_session_id, (
        "with_updates() should preserve session_id"
    )
    
    # 3. Test GameState creation with existing session_id
    new_state = GameState(
        session_id=original_session_id,
        section_number=3
    )
    print(f"New state session_id: {new_state.session_id}")
    assert new_state.session_id == original_session_id, (
        "New GameState should use provided session_id"
    )
    
    # 4. Verify other fields are updated correctly
    assert updated_state.player_input == "test input", "Player input should be updated"
    assert updated_state.section_number == 2, "Section number should be updated"
    print("All session_id tests passed successfully!")
