"""
Test module for narrative content updates in GameState.
"""
import pytest
from datetime import datetime
from models.game_state import GameState
from models.narrator_model import NarratorModel, SourceType as NarratorSourceType
from agents.factories.model_factory import ModelFactory
from models.rules_model import RulesModel, DiceType, SourceType as RulesSourceType, Choice, ChoiceType
from models.errors_model import StateError

def test_narrative_content_initialization(model_factory):
    """Test that narrative content is properly initialized in GameState."""
    # Create a GameState with default narrative
    game_state = model_factory.create_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        narrative=model_factory.create_narrator_model(
            section_number=1,
            content="initialized",
            source_type=NarratorSourceType.RAW
        )
    )
    
    # Verify that narrative is initialized
    assert game_state.narrative is not None
    assert game_state.narrative.content == "initialized"
    assert game_state.narrative.source_type == NarratorSourceType.RAW
    assert game_state.narrative.section_number == game_state.section_number

def test_narrative_content_update(model_factory):
    """Test that narrative content can be updated in GameState."""
    # Create initial GameState with narrative
    initial_state = model_factory.create_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        narrative=model_factory.create_narrator_model(
            section_number=1,
            content="initial content",
            source_type=NarratorSourceType.RAW
        )
    )
    
    # Create updated narrative model
    updated_narrative = NarratorModel(
        section_number=1,  # Must match GameState section_number
        content="Updated narrative content",
        source_type=NarratorSourceType.PROCESSED,
        timestamp=datetime.now(),
        last_update=datetime.now()
    )
    
    # Create new GameState with updated narrative
    updated_state = GameState(
        game_id=initial_state.game_id,
        session_id=initial_state.session_id,
        section_number=1,  # Must match narrative section_number
        narrative=updated_narrative,
        rules=initial_state.rules,
        decision=initial_state.decision,
        trace=initial_state.trace
    )
    
    # Verify that narrative content is updated
    assert updated_state.narrative.content == "Updated narrative content"
    assert updated_state.narrative.source_type == NarratorSourceType.PROCESSED
    assert updated_state.narrative != initial_state.narrative
    assert updated_state.narrative.section_number == updated_state.section_number

def test_narrative_content_preservation(model_factory):
    """Test that narrative content is preserved when updating other state components."""
    # Create initial state with narrative content
    narrative = model_factory.create_narrator_model(
        section_number=1,
        content="Initial narrative content",
        source_type=NarratorSourceType.PROCESSED
    )
    
    initial_state = model_factory.create_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        narrative=narrative
    )
    
    # Create a new rules model
    rules = RulesModel(
        section_number=1,
        dice_type=DiceType.NONE,
        needs_dice=False,
        needs_user_response=True,
        source_type=RulesSourceType.PROCESSED
    )
    
    # Update state with rules
    updated_state = initial_state.with_updates(rules=rules)
    
    # Verify that narrative content is preserved
    assert updated_state.narrative is not None
    assert updated_state.narrative.content == "Initial narrative content"
    assert updated_state.narrative.source_type == NarratorSourceType.PROCESSED
    
    # Create new state with updated narrative for the new section
    updated_narrative = NarratorModel(
        section_number=2,
        content="Initial narrative content",
        source_type=NarratorSourceType.PROCESSED,
        timestamp=initial_state.narrative.timestamp,
        last_update=initial_state.narrative.last_update
    )
    
    # Create new state with updated section number and matching narrative
    updated_state = GameState(
        game_id=initial_state.game_id,
        session_id=initial_state.session_id,
        section_number=2,
        narrative=updated_narrative,
        rules=initial_state.rules,
        decision=initial_state.decision,
        trace=initial_state.trace
    )
    
    # Verify narrative content is preserved while section number is updated
    assert updated_state.narrative.content == "Initial narrative content"
    assert updated_state.narrative.source_type == NarratorSourceType.PROCESSED
    assert updated_state.narrative.section_number == updated_state.section_number
    assert updated_state.section_number == 2

def test_narrative_content_validation(model_factory):
    """Test that GameState synchronizes its section_number with NarratorModel."""
    # Créer un état avec des sections cohérentes
    initial_state = model_factory.create_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        narrative=model_factory.create_narrator_model(section_number=1),
        rules=model_factory.create_rules_model(section_number=1)
    )
    
    # Tenter de mettre à jour avec une section incohérente
    new_narrative = model_factory.create_narrator_model(
        section_number=2,
        content="Test content",
        source_type=NarratorSourceType.RAW
    )
    
    # La mise à jour devrait échouer
    with pytest.raises(StateError, match="Section number mismatch"):
        initial_state.with_updates(narrative=new_narrative)
    
    # Mais la mise à jour devrait fonctionner si on met à jour tout en même temps
    new_rules = model_factory.create_rules_model(section_number=2)
    updated_state = initial_state.with_updates(
        section_number=2,
        narrative=new_narrative,
        rules=new_rules
    )
    
    # Tout doit être synchronisé
    assert updated_state.section_number == 2
    assert updated_state.narrative.section_number == 2
    assert updated_state.rules.section_number == 2
    
    # L'état initial ne doit pas être modifié
    assert initial_state.section_number == 1
    assert initial_state.narrative.section_number == 1
    assert initial_state.rules.section_number == 1

def test_narrative_content_merge(model_factory):
    """Test que le contenu narratif est préservé lors des mises à jour internes."""
    # Créer un état initial avec un contenu narratif important
    initial_state = model_factory.create_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        narrative=model_factory.create_narrator_model(
            section_number=1,
            content="Important narrative content",
            source_type=NarratorSourceType.PROCESSED
        )
    )
    
    # Mettre à jour l'état avec de nouvelles règles
    updated_state = initial_state.with_updates(
        rules=model_factory.create_rules_model(
            section_number=1,
            dice_type=DiceType.COMBAT
        )
    )
    
    # Le contenu narratif devrait être préservé
    assert updated_state.narrative.content == "Important narrative content"
    assert updated_state.narrative.source_type == NarratorSourceType.PROCESSED
    
    # Les IDs devraient être préservés
    assert updated_state.game_id == "test_game"
    assert updated_state.session_id == "test_session"
    
    # Les sections devraient rester cohérentes
    assert updated_state.section_number == updated_state.narrative.section_number == 1
    
    # L'état original ne devrait pas être modifié
    assert initial_state.narrative.content == "Important narrative content"
    assert initial_state.narrative.source_type == NarratorSourceType.PROCESSED

def test_narrative_content_choice_update(model_factory):
    """Test que le contenu narratif est correctement mis à jour lors d'un choix menant à une nouvelle section."""
    # Créer l'état initial avec un choix vers section 2
    initial_state = model_factory.create_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        narrative=model_factory.create_narrator_model(
            section_number=1,
            content="Initial section content",
            source_type=NarratorSourceType.PROCESSED
        ),
        rules=model_factory.create_rules_model(
            section_number=1,
            choices=[
                Choice(
                    text="Go to section 2",
                    type=ChoiceType.DIRECT,
                    target_section=2
                )
            ]
        )
    )
    
    # Créer le nouveau contenu narratif pour la section 2
    new_narrative = model_factory.create_narrator_model(
        section_number=2,
        content="Section 2 content after choice",
        source_type=NarratorSourceType.PROCESSED
    )
    
    # Créer les nouvelles règles pour la section 2
    new_rules = model_factory.create_rules_model(section_number=2)
    
    # Mettre à jour l'état avec la nouvelle section
    updated_state = initial_state.with_updates(
        section_number=2,
        narrative=new_narrative,
        rules=new_rules
    )
    
    # Vérifier la synchronisation des sections
    assert updated_state.section_number == 2
    assert updated_state.narrative.section_number == 2
    assert updated_state.rules.section_number == 2
    
    # Vérifier le contenu narratif
    assert updated_state.narrative.content == "Section 2 content after choice"
    assert updated_state.narrative.source_type == NarratorSourceType.PROCESSED
    
    # Vérifier que l'état initial n'est pas modifié
    assert initial_state.section_number == 1
    assert initial_state.narrative.section_number == 1
    assert initial_state.narrative.content == "Initial section content"
    assert len(initial_state.rules.choices) == 1
    assert initial_state.rules.choices[0].target_section == 2