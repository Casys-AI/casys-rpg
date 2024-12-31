"""
Tests for ID preservation in GameState.
"""
import pytest
from datetime import datetime

from models.game_state import GameState
from models.narrator_model import NarratorModel
from models.rules_model import RulesModel, DiceType, SourceType
from models.errors_model import StateError
from tests.models.conftest import ModelFactory

@pytest.mark.asyncio
async def test_id_preservation():
    """Test que les IDs sont préservés lors des opérations."""
    # État initial
    initial_state = ModelFactory.create_test_game_state(
        game_id="test_game_id",
        session_id="test_session_id"
    )
    
    # Vérification des IDs initiaux
    assert initial_state.game_id == "test_game_id"
    assert initial_state.session_id == "test_session_id"
    
    # Mise à jour avec nouveau contenu
    updated_state = initial_state.model_copy(update={
        "narrative": ModelFactory.create_test_narrator_model(
            content="Updated content"
        )
    })
    
    # Vérification que les IDs sont préservés
    assert updated_state.game_id == initial_state.game_id
    assert updated_state.session_id == initial_state.session_id
