"""
Tests for game state operations.

These tests cover addition, updates, immutability, serialization, and validation errors.
"""
import pytest
from datetime import datetime
from typing import Dict, Any

from models.game_state import GameState
from models.narrator_model import NarratorModel, SourceType
from models.rules_model import RulesModel, DiceType, ChoiceType
from models.decision_model import DecisionModel
from models.trace_model import TraceModel
from models.character_model import CharacterModel
from models.errors_model import StateError
from tests.models.conftest import ModelFactory

@pytest.fixture
def model_factory():
    return ModelFactory()

def test_game_state_addition(model_factory):
    """Test addition of two GameStates."""
    # Create initial state
    state1 = model_factory.create_test_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        narrative=model_factory.create_test_narrator_model(
            section_number=1,
            content=model_factory.create_narrative_content(
                raw_text="Initial content"
            )
        )
    )
    
    # Create update state
    state2 = model_factory.create_test_game_state(
        section_number=2,
        narrative=model_factory.create_test_narrator_model(
            section_number=2,
            content=model_factory.create_narrative_content(
                raw_text="Updated content"
            )
        )
    )
    
    # Combine states
    combined = state1 + state2
    
    # Verify basic properties
    assert combined.game_id == state1.game_id
    assert combined.session_id == state1.session_id
    assert combined.section_number == 2
    assert combined.narrative.content.raw_text == "Updated content"

def test_game_state_model_update(model_factory):
    """Test updating internal models."""
    # Create initial state with all models
    initial = model_factory.create_test_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        narrative=model_factory.create_test_narrator_model(
            section_number=1,
            content=model_factory.create_narrative_content(
                raw_text="Initial narrative"
            )
        ),
        rules=model_factory.create_rules_model(
            section_number=1,
            dice_type=DiceType.NONE
        ),
        decisions=model_factory.create_decision_model(
            section_number=1,
            decision_type=ChoiceType.CHOICE
        ),
        traces=model_factory.create_trace_model(
            section_number=1
        )
    )
    
    # Create update state
    update = model_factory.create_test_game_state(
        section_number=2,
        narrative=model_factory.create_test_narrator_model(
            section_number=2,
            content=model_factory.create_narrative_content(
                raw_text="Updated narrative"
            )
        ),
        rules=model_factory.create_rules_model(
            section_number=2,
            dice_type=DiceType.D6
        ),
        decisions=model_factory.create_decision_model(
            section_number=2,
            decision_type=ChoiceType.DICE
        )
    )
    
    # Combine and verify
    result = initial + update
    assert result.narrative.content.raw_text == "Updated narrative"
    assert result.rules.dice_type == DiceType.D6
    assert result.decisions.decision_type == ChoiceType.DICE
    assert result.section_number == 2
    # Traces should accumulate
    assert result.traces is not None

def test_game_state_partial_update(model_factory):
    """Test updating only some models."""
    # Create initial state
    initial = model_factory.create_test_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        narrative=model_factory.create_test_narrator_model(section_number=1),
        rules=model_factory.create_rules_model(section_number=1)
    )
    
    # Create update with only narrative
    update = model_factory.create_test_game_state(
        section_number=2,
        narrative=model_factory.create_test_narrator_model(section_number=2)
    )
    
    # Combine and verify
    result = initial + update
    assert result.section_number == 2
    assert result.narrative.section_number == 2
    assert result.rules.section_number == 1  # Unchanged

def test_game_state_character_persistence(model_factory):
    """Test character state persistence across updates."""
    # Create initial state with character
    char = model_factory.create_character(
        name="Hero",
        stats=model_factory.create_character_stats(
            endurance=25,
            chance=15,
            skill=20
        )
    )
    
    initial = model_factory.create_test_game_state(
        section_number=1,
        character=char
    )
    
    # Create update without character
    update = model_factory.create_test_game_state(section_number=2)
    
    # Combine and verify
    result = initial + update
    assert result.character.name == "Hero"
    assert result.character.stats.endurance == 25
    assert result.character.stats.chance == 15
    assert result.character.stats.skill == 20

def test_game_state_trace_accumulation(model_factory):
    """Test accumulation of trace actions."""
    # Create initial state with trace
    initial = model_factory.create_test_game_state(
        section_number=1,
        traces=model_factory.create_trace_model(
            section_number=1,
            actions=[
                model_factory.create_action(
                    type=ActionType.USER_INPUT,
                    description="Initial action"
                )
            ]
        )
    )
    
    # Create update with new trace
    update = model_factory.create_test_game_state(
        section_number=2,
        traces=model_factory.create_trace_model(
            section_number=2,
            actions=[
                model_factory.create_action(
                    type=ActionType.DICE_ROLL,
                    description="Update action"
                )
            ]
        )
    )
    
    # Combine and verify
    result = initial + update
    assert len(result.traces.actions) == 2
    assert result.traces.actions[0].description == "Initial action"
    assert result.traces.actions[1].description == "Update action"

def test_game_state_validation_errors(model_factory):
    """Test validation errors in game state operations."""
    # Create states with mismatched section numbers
    state1 = model_factory.create_test_game_state(
        section_number=1,
        narrative=model_factory.create_test_narrator_model(section_number=1)
    )
    
    invalid_state = model_factory.create_test_game_state(
        section_number=2,
        narrative=model_factory.create_test_narrator_model(section_number=3)
    )
    
    # Test section number mismatch
    with pytest.raises(StateError, match="Section number mismatch"):
        state1 + invalid_state

def test_game_state_immutability(model_factory):
    """Test immutability of game state."""
    # Create initial state
    initial = model_factory.create_test_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1
    )
    
    # Create update
    update = model_factory.create_test_game_state(section_number=2)
    
    # Combine states
    result = initial + update
    
    # Verify original states are unchanged
    assert initial.section_number == 1
    assert update.section_number == 2
    assert result.section_number == 2

def test_game_state_serialization(model_factory):
    """Test game state serialization."""
    # Create state with all components
    state = model_factory.create_test_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        character=model_factory.create_character(),
        narrative=model_factory.create_test_narrator_model(),
        rules=model_factory.create_rules_model(),
        decisions=model_factory.create_decision_model(),
        traces=model_factory.create_trace_model()
    )
    
    # Serialize
    state_dict = state.model_dump()
    
    # Verify structure
    assert isinstance(state_dict, dict)
    assert state_dict["game_id"] == "test_game"
    assert state_dict["session_id"] == "test_session"
    assert state_dict["section_number"] == 1
    assert isinstance(state_dict["character"], dict)
    assert isinstance(state_dict["narrative"], dict)
    assert isinstance(state_dict["rules"], dict)
    assert isinstance(state_dict["decisions"], dict)
    assert isinstance(state_dict["traces"], dict)
