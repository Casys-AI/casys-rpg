"""Test section number synchronization between models."""

import pytest
from datetime import datetime

from models.game_state import GameState
from models.rules_model import RulesModel, DiceType, SourceType
from models.narrator_model import NarratorModel
from models.decision_model import DecisionModel
from models.errors_model import StateError

def test_section_number_sync(model_factory):
    """Test la synchronisation des numéros de section."""
    # Créer les modèles initiaux
    narrator_section_2 = model_factory.create_narrator_model(
        section_number=2,
        content="Content for section 2"
    )
    
    rules_section_2 = model_factory.create_rules_model(
        section_number=2,
        dice_type=DiceType.NONE,
        source_type=SourceType.RAW
    )
    
    # Premier état avec section 2
    initial_state = model_factory.create_game_state(
        section_number=2,
        narrative=narrator_section_2,
        rules=rules_section_2
    )
    
    assert initial_state.section_number == 2, "Initial section should be 2"
    
    # Simuler le workflow qui cause le problème
    with pytest.raises(StateError, match="Section number mismatch"):
        model_factory.create_game_state(
            section_number=[2, 2, 2],  # LangGraph accumule les sections
            narrative=[narrator_section_2, narrator_section_2],  # LangGraph essaie d'additionner
            rules=[rules_section_2, rules_section_2]  # LangGraph essaie d'additionner
        )
    
    # Test la préservation des numéros de section lors des mises à jour
    new_narrative = model_factory.create_narrator_model(
        section_number=2,
        content="New content"
    )
    
    updated_state = initial_state.model_copy(update={
        "narrative": new_narrative
    })
    
    assert updated_state.section_number == 2, "Section should stay 2"
    assert updated_state.narrative.section_number == 2, "Narrative section should stay 2"
    assert updated_state.rules.section_number == 2, "Rules section should stay 2"

def test_section_number_update(model_factory):
    """Test la mise à jour correcte des numéros de section."""
    initial_state = model_factory.create_game_state(
        section_number=1,
        narrative=model_factory.create_narrator_model(
            section_number=1,
            content="Initial content"
        )
    )
    
    update_state = model_factory.create_game_state(
        section_number=2,
        narrative=model_factory.create_narrator_model(
            section_number=2,
            content="Updated content"
        )
    )
    
    combined_state = initial_state + update_state
    assert combined_state.section_number == 2, "Should take new section number"
    assert combined_state.narrative.section_number == 2, "Narrative should update section"
    assert combined_state.narrative.content == "Updated content", "Content should update"

def test_section_number_validation(model_factory):
    """Test la validation des numéros de section entre les modèles."""
    # Test avec des numéros de section différents
    with pytest.raises(StateError, match="Section number mismatch"):
        model_factory.create_game_state(
            section_number=1,
            narrative=model_factory.create_narrator_model(section_number=2)
        )
    
    with pytest.raises(StateError, match="Section number mismatch"):
        model_factory.create_game_state(
            section_number=1,
            rules=model_factory.create_rules_model(section_number=2)
        )
    
    with pytest.raises(StateError, match="Section number mismatch"):
        model_factory.create_game_state(
            section_number=1,
            decision=model_factory.create_decision_model(section_number=2)
        )

def test_section_number_preservation(model_factory):
    """Test la préservation des numéros de section lors des mises à jour."""
    initial_state = model_factory.create_game_state(
        section_number=1,
        narrative=model_factory.create_narrator_model(section_number=1),
        rules=model_factory.create_rules_model(section_number=1),
        decision=model_factory.create_decision_model(section_number=1)
    )
    
    # Mise à jour avec un nouveau narrateur
    new_narrative = model_factory.create_narrator_model(
        section_number=2,
        content="New content"
    )
    
    # La mise à jour devrait échouer car les sections ne correspondent pas
    with pytest.raises(StateError, match="Section number mismatch"):
        initial_state.model_copy(update={
            "narrative": new_narrative
        })
