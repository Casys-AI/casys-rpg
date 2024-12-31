"""
Tests for GameState operations (addition, updates).
"""
import pytest
from datetime import datetime

from models.game_state import GameState
from models.narrator_model import NarratorModel
from models.rules_model import RulesModel, DiceType, SourceType
from tests.test_model_factory import TestModelFactory

def test_game_state_addition():
    """Test l'addition de deux GameState."""
    state1 = TestModelFactory.create_test_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        narrative=TestModelFactory.create_test_narrator_model(
            content="Content 1"
        )
    )
    
    state2 = TestModelFactory.create_test_game_state(
        section_number=2,
        narrative=TestModelFactory.create_test_narrator_model(
            content="Content 2"
        )
    )
    
    combined = state1 + state2
    assert combined.game_id == state1.game_id
    assert combined.session_id == state1.session_id
    assert combined.section_number == 2
    assert combined.narrative.content == "Content 2"

def test_game_state_model_update():
    """Test la mise à jour des modèles internes."""
    initial = TestModelFactory.create_test_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        narrative=TestModelFactory.create_test_narrator_model(
            content="Initial"
        ),
        rules=TestModelFactory.create_test_rules_model(
            dice_type=DiceType.NONE
        )
    )
    
    update = TestModelFactory.create_test_game_state(
        section_number=2,
        narrative=TestModelFactory.create_test_narrator_model(
            content="Updated"
        ),
        rules=TestModelFactory.create_test_rules_model(
            dice_type=DiceType.D6
        )
    )
    
    result = initial + update
    assert result.narrative.content == "Updated"
    assert result.rules.dice_type == DiceType.D6
    assert result.section_number == 2
