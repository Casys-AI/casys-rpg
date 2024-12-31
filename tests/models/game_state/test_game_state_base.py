"""
Tests for basic GameState functionality.
"""
import pytest
from datetime import datetime

from models.game_state import GameState
from models.narrator_model import NarratorModel
from models.rules_model import RulesModel, DiceType, SourceType
from models.errors_model import StateError
from tests.test_model_factory import TestModelFactory

def test_game_state_creation():
    """Test la création basique d'un GameState."""
    state = TestModelFactory.create_test_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1
    )
    
    assert state.game_id == "test_game"
    assert state.session_id == "test_session"
    assert state.section_number == 1

def test_game_state_validation():
    """Test la validation des champs du GameState."""
    with pytest.raises(ValueError):
        TestModelFactory.create_test_game_state(section_number=-1)
        
    with pytest.raises(ValueError):
        TestModelFactory.create_test_game_state(section_number=0)

def test_game_state_model_consistency():
    """Test la cohérence entre les modèles internes."""
    state = TestModelFactory.create_test_game_state(
        section_number=2,
        narrative=TestModelFactory.create_test_narrator_model(
            section_number=2,
            content="Test content"
        ),
        rules=TestModelFactory.create_test_rules_model(
            section_number=2,
            dice_type=DiceType.NONE
        )
    )
    
    assert state.section_number == state.narrative.section_number
    assert state.section_number == state.rules.section_number
