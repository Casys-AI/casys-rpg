"""
Tests for game state model operations (addition, combination).
"""
import pytest
from datetime import datetime

from models.game_state import GameState
from models.narrator_model import NarratorModel
from models.rules_model import RulesModel, DiceType, SourceType
from models.errors_model import StateError
from tests.test_model_factory import TestModelFactory

def test_model_addition():
    """Test l'addition de modèles."""
    # Test NarratorModel addition
    narrator1 = TestModelFactory.create_test_narrator_model(
        section_number=1,
        content="Content 1"
    )
    narrator2 = TestModelFactory.create_test_narrator_model(
        section_number=2,
        content="Content 2"
    )
    
    combined_narrator = narrator1 + narrator2
    assert combined_narrator.section_number == 2, "Should take second section number"
    assert combined_narrator.content == "Content 2", "Should take second content"
    
    # Test RulesModel addition
    rules1 = TestModelFactory.create_test_rules_model(
        section_number=1,
        dice_type=DiceType.NONE
    )
    rules2 = TestModelFactory.create_test_rules_model(
        section_number=2,
        dice_type=DiceType.D6
    )
    
    combined_rules = rules1 + rules2
    assert combined_rules.section_number == 2, "Should take second section number"
    assert combined_rules.dice_type == DiceType.D6, "Should take second dice type"

def test_gamestate_combination():
    """Test la combinaison d'états de jeu."""
    state1 = TestModelFactory.create_test_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        narrative=TestModelFactory.create_test_narrator_model(
            content="Initial content"
        )
    )
    
    state2 = TestModelFactory.create_test_game_state(
        section_number=2,
        narrative=TestModelFactory.create_test_narrator_model(
            content="Updated content"
        )
    )
    
    combined_state = state1 + state2
    assert combined_state.game_id == state1.game_id, "Should keep original game_id"
    assert combined_state.session_id == state1.session_id, "Should keep original session_id"
    assert combined_state.section_number == 2, "Should take new section number"
    assert combined_state.narrative.content == "Updated content", "Should update content"
