"""
Test module for narrative content updates in GameState.
"""
import pytest
from datetime import datetime
from models.game_state import GameState
from models.narrator_model import NarratorModel, SourceType as NarratorSourceType
from agents.factories.model_factory import ModelFactory
from models.rules_model import RulesModel, SourceType as RulesSourceType
from models.dice_model import DiceType

def test_narrative_content_initialization():
    """Test that narrative content is properly initialized in GameState."""
    # Create a GameState with default narrative
    game_state = ModelFactory.create_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1
    )
    
    # Verify that narrative is initialized
    assert game_state.narrative is not None
    assert game_state.narrative.content == "initialized"
    assert game_state.narrative.source_type == NarratorSourceType.RAW
    assert game_state.narrative.section_number == game_state.section_number

def test_narrative_content_update():
    """Test that narrative content can be updated in GameState."""
    # Create initial GameState
    initial_state = ModelFactory.create_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1
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

def test_narrative_content_preservation():
    """Test that narrative content is preserved when updating other state components."""
    # Create initial state with narrative content
    narrative = NarratorModel(
        section_number=1,
        content="Initial narrative content",
        source_type=NarratorSourceType.PROCESSED
    )
    
    initial_state = ModelFactory.create_game_state(
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

def test_narrative_content_validation():
    """Test that GameState synchronizes its section_number with NarratorModel."""
    # Create a NarratorModel with section 2
    narrative = NarratorModel(
        section_number=2,
        content="Test content",
        source_type=NarratorSourceType.RAW
    )
    
    # GameState devrait synchroniser son section_number avec celui du NarratorModel
    state = GameState(
        game_id="test_game",
        session_id="test_session",
        section_number=1,  # Sera synchronisé avec narrative.section_number
        narrative=narrative
    )
    
    # Vérifier que le GameState a bien synchronisé son section_number
    assert state.section_number == narrative.section_number == 2
    
    # Vérifier que le RulesModel est aussi synchronisé si présent
    rules = RulesModel(
        section_number=2,
        dice_type=DiceType.D20,
        source_type=RulesSourceType.RAW
    )
    state.rules = rules
    
    # Tout doit être synchronisé
    assert state.section_number == state.narrative.section_number == state.rules.section_number == 2

def test_narrative_content_merge():
    """Test that narrative content is preserved during state merges."""
    # Create first state with meaningful narrative
    narrative1 = NarratorModel(
        section_number=1,
        content="Important narrative content",
        source_type=NarratorSourceType.PROCESSED,
        timestamp=datetime.now(),
        last_update=datetime.now()
    )
    state1 = ModelFactory.create_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        narrative=narrative1
    )
    
    # Create second state with initialized narrative
    narrative2 = NarratorModel(
        section_number=1,
        content="initialized",
        source_type=NarratorSourceType.RAW,
        timestamp=datetime.now(),
        last_update=datetime.now()
    )
    state2 = ModelFactory.create_game_state(
        game_id="test_game2",
        session_id="test_session2",
        section_number=1,
        narrative=narrative2
    )
    
    # Create rules for state2
    rules2 = RulesModel(
        section_number=1,
        dice_type=DiceType.NONE,
        needs_dice=False,
        needs_user_response=True,
        source_type=RulesSourceType.PROCESSED
    )
    state2 = state2.with_updates(rules=rules2)
    
    # Merge states
    merged_state = state1 + state2
    
    # Verify that important narrative content is preserved
    assert merged_state.narrative.content == "Important narrative content"
    assert merged_state.narrative.source_type == NarratorSourceType.PROCESSED
    assert merged_state.rules == rules2  # Rules from state2 should be present

```
