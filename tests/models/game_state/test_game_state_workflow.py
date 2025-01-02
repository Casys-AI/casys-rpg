"""
Tests for GameState in workflow context.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock

from models.game_state import GameState
from models.narrator_model import NarratorModel
from models.rules_model import RulesModel, DiceType, SourceType
from models.errors_model import StateError
from tests.models.conftest import ModelFactory
from config.storage_config import StorageConfig
from managers.cache_manager import CacheManager
from managers.state_manager import StateManager
from managers.rules_manager import RulesManager
from managers.workflow_manager import WorkflowManager
from managers.character_manager import CharacterManager

@pytest.mark.asyncio
async def test_workflow_state_initialization():
    """Test l'initialisation correcte de l'état dans le workflow."""
    config = StorageConfig()
    cache_manager = CacheManager(config)
    character_manager = CharacterManager(config, cache_manager)
    state_manager = StateManager(config, cache_manager, character_manager)
    await state_manager.initialize()  # Important: initialiser le state manager
    
    rules_manager = RulesManager(config, cache_manager)
    workflow_manager = WorkflowManager(state_manager, rules_manager)
    
    initial_state = ModelFactory.create_test_game_state(
        game_id="test_game_id",
        session_id="test_session_id"
    )
    
    workflow_state = await workflow_manager.start_workflow(initial_state)
    assert workflow_state.game_id == initial_state.game_id
    assert workflow_state.session_id == initial_state.session_id

@pytest.mark.asyncio
async def test_workflow_state_update():
    """Test la mise à jour de l'état dans le workflow."""
    config = StorageConfig()
    cache_manager = CacheManager(config)
    character_manager = CharacterManager(config, cache_manager)
    state_manager = StateManager(config, cache_manager, character_manager)
    await state_manager.initialize()
    
    rules_manager = RulesManager(config, cache_manager)
    workflow_manager = WorkflowManager(state_manager, rules_manager)
    
    # État initial
    initial_state = ModelFactory.create_test_game_state(
        game_id="test_game_id",
        session_id="test_session_id",
        section_number=1,
        narrative=ModelFactory.create_test_narrator_model(
            content="Initial section"
        )
    )
    
    # Démarrer le workflow
    workflow_state = await workflow_manager.start_workflow(initial_state)
    
    # Mise à jour
    update_state = ModelFactory.create_test_game_state(
        section_number=2,
        narrative=ModelFactory.create_test_narrator_model(
            section_number=2,
            content="Updated section"
        )
    )
    
    # Vérifier la mise à jour
    final_state = workflow_state + update_state
    assert final_state.game_id == initial_state.game_id
    assert final_state.session_id == initial_state.session_id
    assert final_state.section_number == 2
    assert final_state.narrative.content == "Updated section"
