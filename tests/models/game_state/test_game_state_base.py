"""
Tests for basic GameState functionality.
"""
import pytest
from datetime import datetime
from typing import Dict, Any

from models.game_state import GameState, GameStateInput
from models.errors_model import StateError
from models.narrator_model import NarratorModel, SourceType
from models.rules_model import RulesModel, DiceType, ChoiceType
from models.decision_model import DecisionModel
from models.trace_model import TraceModel
from models.character_model import CharacterModel

def test_game_state_creation(model_factory):
    """Test creating a game state with all fields."""
    # Create a basic game state
    basic_state = GameState(
        game_id="test_game",
        session_id="test_session",
        section_number=1
    )
    assert basic_state.game_id == "test_game"
    assert basic_state.session_id == "test_session"
    assert basic_state.section_number == 1
    assert basic_state.character is None
    assert basic_state.narrative is None
    assert basic_state.rules is None
    assert basic_state.trace is None
    assert basic_state.player_input is None

    # Create a full game state with all optional fields
    full_state = model_factory.create_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        character=model_factory.create_character(),
        narrative=model_factory.create_narrator_model(),
        rules=model_factory.create_rules_model(),
        trace=model_factory.create_trace_model(),
        player_input="test input"
    )
    
    # Check all fields are set
    assert full_state.game_id == "test_game"
    assert full_state.session_id == "test_session"
    assert full_state.section_number == 1
    assert full_state.character is not None
    assert full_state.narrative is not None
    assert full_state.rules is not None
    assert full_state.trace is not None
    assert isinstance(full_state.trace.start_time, datetime)
    assert isinstance(full_state.trace.history, list)
    assert full_state.player_input == "test input"

def test_game_state_validation(model_factory):
    """Test validation of GameState fields."""
    # Test invalid section number
    with pytest.raises(ValueError, match="Section number must be positive"):
        GameStateInput(
            game_id="test_game",
            session_id="test_session",
            section_number=-1
        )
    
    with pytest.raises(ValueError, match="Section number must be positive"):
        GameStateInput(
            game_id="test_game",
            session_id="test_session",
            section_number=0
        )

    # Test valid section number
    state = GameStateInput(
        game_id="test_game",
        session_id="test_session",
        section_number=1
    )
    assert state.section_number == 1

def test_game_state_model_consistency(model_factory):
    """Test consistency between internal models."""
    # Create models with different section numbers
    state = model_factory.create_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        narrative=model_factory.create_narrator_model(section_number=1),
        rules=model_factory.create_rules_model(section_number=1),
        trace=model_factory.create_trace_model(section_number=1)
    )
    
    # Verify section numbers are synchronized
    assert state.section_number == 1
    assert state.narrative.section_number == 1
    assert state.rules.section_number == 1
    assert state.trace.section_number == 1

def test_game_state_update(model_factory):
    """Test updating GameState fields."""
    initial_state = model_factory.create_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1
    )
    
    # Update with new values
    updated_state = initial_state.with_updates(
        section_number=2,
        player_input="new input"
    )
    
    # Verify updates
    assert updated_state.section_number == 2
    assert updated_state.player_input == "new input"
    assert updated_state.game_id == initial_state.game_id
    assert updated_state.session_id == initial_state.session_id

def test_game_state_validation_error(model_factory):
    """Test validation errors in GameState."""
    with pytest.raises(ValueError):
        model_factory.create_game_state(
            game_id="",  # Invalid empty game_id
            session_id="test_session",
            section_number=1
        )

def test_game_state_serialization(model_factory):
    """Test serialization of GameState."""
    state = model_factory.create_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        character=model_factory.create_character(),
        narrative=model_factory.create_narrator_model(),
        rules=model_factory.create_rules_model(),
        trace=model_factory.create_trace_model()
    )
    
    # Test serialization
    serialized = state.model_dump()
    assert isinstance(serialized, dict)
    assert serialized["game_id"] == "test_game"
    assert serialized["session_id"] == "test_session"
    assert serialized["section_number"] == 1
    
    # Test JSON serialization
    json_str = state.model_dump_json()
    assert isinstance(json_str, str)
    assert "test_game" in json_str
    assert "test_session" in json_str

def test_game_state_with_player_input(model_factory):
    """Test GameState with player input."""
    state = model_factory.create_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        player_input="test input"
    )
    
    assert state.player_input == "test input"
    
    # Test input state conversion
    input_state = state.to_input()
    assert input_state.player_input == "test input"

def test_game_state_optional_fields(model_factory):
    """Test GameState with missing optional fields."""
    # Create state with minimal fields
    state = model_factory.create_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1
    )
    
    # Verify optional fields are None
    assert state.character is None
    assert state.narrative is None
    assert state.rules is None
    assert state.trace is None
    assert state.player_input is None
    assert state.metadata is None
    
    # Verify state is still valid
    state.validate_state()
