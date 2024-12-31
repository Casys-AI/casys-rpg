"""
Tests for game state section number synchronization.
"""
import pytest
from datetime import datetime

from models.game_state import GameState
from models.narrator_model import NarratorModel
from models.rules_model import RulesModel, DiceType, SourceType
from models.errors_model import StateError
from tests.test_model_factory import TestModelFactory

def test_section_number_sync():
    """Test la synchronisation des numéros de section."""
    # Créer les modèles initiaux
    narrator_section_2 = NarratorModel(
        section_number=2,
        content="Content for section 2",
        source_type=SourceType.RAW
    )
    
    rules_section_2 = RulesModel(
        section_number=2,
        dice_type=DiceType.NONE,
        source_type=SourceType.RAW
    )
    
    # Premier état avec section 2
    state_dict_1 = {
        'game_id': 'test_game',
        'session_id': 'test',
        'section_number': 2,
        'narrative': narrator_section_2,
        'rules': rules_section_2
    }
    
    game_state_1 = GameState(**state_dict_1)
    assert game_state_1.section_number == 2, "Initial section should be 2"
    
    # Simuler le workflow qui cause le problème
    state_dict_2 = {
        'game_id': 'test_game',
        'session_id': 'test',
        'section_number': [2, 2, 2],  # LangGraph accumule les sections
        'narrative': [narrator_section_2, narrator_section_2],  # LangGraph essaie d'additionner
        'rules': [rules_section_2, rules_section_2]  # LangGraph essaie d'additionner
    }
    
    game_state_2 = GameState(**state_dict_2)
    assert game_state_2.section_number == 2, "Section should stay 2, not 6"
    assert game_state_2.narrative.section_number == 2, "Narrative section should stay 2"
    assert game_state_2.rules.section_number == 2, "Rules section should stay 2"

def test_section_number_update():
    """Test la mise à jour correcte des numéros de section."""
    initial_state = TestModelFactory.create_test_game_state(
        section_number=1,
        narrative=TestModelFactory.create_test_narrator_model(
            section_number=1,
            content="Initial content"
        )
    )
    
    update_state = TestModelFactory.create_test_game_state(
        section_number=2,
        narrative=TestModelFactory.create_test_narrator_model(
            section_number=2,
            content="Updated content"
        )
    )
    
    combined_state = initial_state + update_state
    assert combined_state.section_number == 2, "Should take new section number"
    assert combined_state.narrative.section_number == 2, "Narrative should update section"
    assert combined_state.narrative.content == "Updated content", "Content should update"
