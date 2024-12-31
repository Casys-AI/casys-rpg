"""
Tests for game state ID preservation functionality.
"""
import pytest
from datetime import datetime

from models.game_state import GameState
from models.errors_model import StateError
from tests.test_model_factory import TestModelFactory
from config.storage_config import StorageConfig
from managers.cache_manager import CacheManager
from managers.state_manager import StateManager
from managers.rules_manager import RulesManager
from managers.workflow_manager import WorkflowManager

@pytest.mark.asyncio
async def test_basic_id_preservation():
    """Test la préservation basique des IDs."""
    initial_state = TestModelFactory.create_test_game_state(
        game_id="test_game_id",
        session_id="test_session_id",
        section_number=1
    )
    
    # Vérifier que les IDs sont préservés après une mise à jour simple
    update_state = TestModelFactory.create_test_game_state(section_number=2)
    combined_state = initial_state + update_state
    
    assert combined_state.game_id == initial_state.game_id
    assert combined_state.session_id == initial_state.session_id

@pytest.mark.asyncio
async def test_model_update_with_id_preservation():
    """Test que la mise à jour des modèles préserve les IDs."""
    initial_state = TestModelFactory.create_test_game_state(
        game_id="test_game_id",
        session_id="test_session_id",
        section_number=1,
        narrative=TestModelFactory.create_test_narrator_model(content="Initial")
    )
    
    # Mise à jour du contenu narratif
    update_state = TestModelFactory.create_test_game_state(
        section_number=2,
        narrative=TestModelFactory.create_test_narrator_model(
            section_number=2,
            content="Updated"
        )
    )
    
    combined_state = initial_state + update_state
    assert combined_state.game_id == initial_state.game_id
    assert combined_state.session_id == initial_state.session_id
    assert combined_state.narrative.content == "Updated"
    assert combined_state.narrative.section_number == 2

@pytest.mark.asyncio
async def test_workflow_state_initialization():
    """Test l'initialisation correcte de l'état dans le workflow."""
    config = StorageConfig()
    cache_manager = CacheManager(config)
    state_manager = StateManager(config, cache_manager)
    await state_manager.initialize()  # Important: initialiser le state manager
    
    rules_manager = RulesManager(config, cache_manager)
    workflow_manager = WorkflowManager(state_manager, rules_manager)
    
    initial_state = TestModelFactory.create_test_game_state(
        game_id="test_game_id",
        session_id="test_session_id"
    )
    
    workflow_state = await workflow_manager.start_workflow(initial_state)
    assert workflow_state.game_id == initial_state.game_id
    assert workflow_state.session_id == initial_state.session_id
