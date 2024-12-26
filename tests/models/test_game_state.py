"""Tests for game state models."""
import pytest
from datetime import datetime
from models.game_state import GameState, GameStateInput, GameStateOutput, first_not_none
from models.narrator_model import NarratorModel
from models.rules_model import RulesModel, SourceType as RulesSourceType

def test_first_not_none_function():
    """Test the first_not_none function behavior."""
    assert first_not_none("a", None) == "a"
    assert first_not_none(None, "b") == "b"
    assert first_not_none(None, None) is None
    assert first_not_none("a", "b") == "a"

def test_game_state_base():
    """Test GameStateBase creation and validation."""
    state = GameState(
        session_id="test_session",
        section_number=1,
        source=RulesSourceType.RAW
    )
    assert state.session_id == "test_session"

def test_game_state_input():
    """Test GameStateInput creation and validation."""
    input_state = GameStateInput(
        session_id="test_session",
        section_number=1,
        player_input="test input"
    )
    assert input_state.section_number == 1
    assert input_state.player_input == "test input"

def test_game_state_output():
    """Test GameStateOutput creation and validation."""
    output_state = GameStateOutput(
        session_id="test_session",
        narrative=NarratorModel(section_number=1),
        rules=RulesModel(section_number=1)
    )
    assert output_state.narrative is not None
    assert output_state.rules is not None

def test_section_number_validation():
    """Test section number validation."""
    # Test valid section number
    game_state = GameState(
        session_id="test_session",
        section_number=1,
        source=RulesSourceType.RAW
    )
    assert game_state.section_number == 1

    # Test section number mismatch
    with pytest.raises(ValueError):
        GameState(
            session_id="test_session",
            section_number=1,
            narrative=NarratorModel(section_number=2),
            source=RulesSourceType.RAW
        )

def test_section_number_sync():
    """Test section number synchronization."""
    game_state = GameState(
        session_id="test_session",
        section_number=1,
        narrative=NarratorModel(section_number=1),
        rules=RulesModel(section_number=1),
        source=RulesSourceType.RAW
    )
    
    # Test sync after update
    game_state.section_number = 2
    game_state.sync_section_numbers()
    assert game_state.narrative.section_number == 2
    assert game_state.rules.section_number == 2

def test_state_conversion():
    """Test state conversion methods."""
    game_state = GameState(
        session_id="test_session",
        section_number=1,
        player_input="test",
        source=RulesSourceType.RAW
    )
    
    # Test to_input
    input_state = game_state.to_input()
    assert isinstance(input_state, GameStateInput)
    assert input_state.section_number == 1
    assert input_state.player_input == "test"
    
    # Test to_output
    output_state = game_state.to_output()
    assert isinstance(output_state, GameStateOutput)
    assert output_state.session_id == "test_session"

def test_error_state_creation():
    """Test error state creation."""
    error_state = GameState.create_error_state(
        error_message="test error",
        session_id="test_session",
        section_number=1
    )
    assert error_state.error == "test error"
    assert error_state.section_number == 1
    assert error_state.session_id == "test_session"

def test_state_updates():
    """Test state update methods."""
    original_state = GameState(
        session_id="test_session",
        section_number=1,
        source=RulesSourceType.RAW
    )
    
    # Test with_updates
    updated_state = original_state.with_updates(section_number=2)
    assert updated_state.section_number == 2
    assert updated_state.session_id == original_state.session_id
