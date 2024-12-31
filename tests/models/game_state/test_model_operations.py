"""Tests for GameState model operations."""
import pytest
from datetime import datetime

from models.game_state import GameState
from models.narrator_model import NarratorModel
from models.rules_model import RulesModel, DiceType, SourceType
from models.decision_model import DecisionModel
from models.trace_model import TraceModel
from models.errors_model import StateError
from tests.models.conftest import ModelFactory

@pytest.mark.asyncio
async def test_model_update():
    """Test la mise à jour des modèles dans GameState."""
    # État initial
    initial_state = ModelFactory.create_test_game_state(
        section_number=1,
        narrative=ModelFactory.create_test_narrator_model(
            content="Initial content"
        )
    )
    
    # Mise à jour avec nouveau contenu
    updated_state = initial_state.model_copy(update={
        "section_number": 2,
        "narrative": ModelFactory.create_test_narrator_model(
            content="Updated content",
            section_number=2
        )
    })
    
    # Vérifications
    assert updated_state.section_number == 2
    assert updated_state.narrative.content == "Updated content"
    assert updated_state.narrative.section_number == 2

@pytest.mark.asyncio
async def test_model_merge():
    """Test la fusion de deux GameState."""
    # États à fusionner
    state1 = ModelFactory.create_test_game_state(
        section_number=1,
        narrative=ModelFactory.create_test_narrator_model(
            content="Content 1"
        )
    )
    
    state2 = ModelFactory.create_test_game_state(
        section_number=2,
        narrative=ModelFactory.create_test_narrator_model(
            content="Content 2",
            section_number=2
        )
    )
    
    # Fusion
    merged_state = state1.model_copy(update=state2.model_dump())
    
    # Vérifications
    assert merged_state.section_number == 2
    assert merged_state.narrative.content == "Content 2"
    assert merged_state.narrative.section_number == 2
