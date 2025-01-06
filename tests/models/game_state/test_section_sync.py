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
    # Créer les modèles initiaux avec des sections cohérentes
    narrator_section_2 = model_factory.create_narrator_model(
        section_number=2,
        content="Content for section 2"
    )
    
    rules_section_2 = model_factory.create_rules_model(  # Même section que le narratif
        section_number=2,
        dice_type=DiceType.NONE,
        source_type=SourceType.RAW
    )
    
    # Créer un modèle de règles avec une section différente pour tester l'erreur
    rules_section_3 = model_factory.create_rules_model(
        section_number=3,
        dice_type=DiceType.NONE,
        source_type=SourceType.RAW
    )
    
    # Premier état avec section 2 (doit être cohérent)
    initial_state = model_factory.create_game_state(
        section_number=2,
        narrative=narrator_section_2,
        rules=rules_section_2  # Utiliser rules_section_2 pour l'état initial
    )
    
    assert initial_state.section_number == 2, "Initial section should be 2"
    
    # Simuler le workflow qui cause le problème
    with pytest.raises(StateError, match="Section number mismatch"):
        model_factory.create_game_state(
            section_number=2,
            narrative=narrator_section_2,
            rules=rules_section_3  # Utiliser rules_section_3 pour provoquer l'erreur
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
    
    update_narrative = model_factory.create_narrator_model(
        section_number=2,
        content="Updated content"
    )
    
    # Utiliser with_updates au lieu de l'opérateur +
    combined_state = initial_state.with_updates(
        section_number=2,
        narrative=update_narrative
    )
    
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
    
    # Test avec des numéros de section cohérents
    state = model_factory.create_game_state(
        section_number=2,
        narrative=model_factory.create_narrator_model(section_number=2),
        rules=model_factory.create_rules_model(section_number=2)
    )
    
    assert state.section_number == 2
    assert state.narrative.section_number == 2
    assert state.rules.section_number == 2

def test_section_number_preservation(model_factory):
    """Test la préservation des numéros de section lors des mises à jour."""
    initial_state = model_factory.create_game_state(
        section_number=1,
        narrative=model_factory.create_narrator_model(section_number=1),
        rules=model_factory.create_rules_model(section_number=1)
    )
    
    # Mise à jour avec un nouveau narrateur sans changer la section
    new_narrative = model_factory.create_narrator_model(
        section_number=2,
        content="New content"
    )
    
    # La mise à jour devrait échouer car les sections ne correspondent pas
    with pytest.raises(StateError, match="Section number mismatch"):
        initial_state.with_updates(narrative=new_narrative)
        
    # Vérifier que l'état initial n'a pas été modifié
    assert initial_state.section_number == 1
    assert initial_state.narrative.section_number == 1
    assert initial_state.rules.section_number == 1
    
    # Mise à jour avec nouvelle section et nouveaux modèles
    new_rules = model_factory.create_rules_model(section_number=2)
    
    # Cette fois ça devrait marcher car on met à jour tout en même temps
    updated_state = initial_state.with_updates(
        section_number=2,
        narrative=new_narrative,
        rules=new_rules
    )
    
    # Vérifier que la mise à jour a réussi
    assert updated_state.section_number == 2, "Section number should be updated"
    assert updated_state.narrative.section_number == 2, "Narrative section should be updated"
    assert updated_state.rules.section_number == 2, "Rules section should be updated"
    assert updated_state.narrative.content == "New content", "Content should be updated"
    
    # Vérifier que l'état initial est toujours intact
    assert initial_state.section_number == 1, "Original section should not change"
    assert initial_state.narrative.section_number == 1, "Original narrative should not change"
    assert initial_state.rules.section_number == 1, "Original rules should not change"
