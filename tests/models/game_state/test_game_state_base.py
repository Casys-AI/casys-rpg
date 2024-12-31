"""
Tests for basic GameState functionality.
"""
import pytest
from datetime import datetime
from typing import Dict, Any

from models.game_state import GameState
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
        model_factory.create_game_state(
            game_id="test_game",
            session_id="test_session",
            section_number=-1
        )
    
    with pytest.raises(ValueError, match="Section number must be positive"):
        model_factory.create_game_state(
            game_id="test_game",
            session_id="test_session",
            section_number=0
        )
    
    # Test empty game_id
    with pytest.raises(ValueError, match="game_id cannot be empty"):
        model_factory.create_game_state(
            game_id="",
            session_id="test_session",
            section_number=1
        )
    
    # Test empty session_id
    with pytest.raises(ValueError, match="session_id cannot be empty"):
        model_factory.create_game_state(
            game_id="test_game",
            session_id="",
            section_number=1
        )

def test_game_state_model_consistency(model_factory):
    """Test consistency between internal models."""
    narrator_model = model_factory.create_narrator_model(section_number=2)
    rules_model = model_factory.create_rules_model(section_number=2)
    
    # Test matching section numbers
    state = model_factory.create_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=2,
        narrative=narrator_model,
        rules=rules_model
    )
    assert state.section_number == state.narrative.section_number
    assert state.section_number == state.rules.section_number
    
    # Test mismatched section numbers
    narrator_model_wrong = model_factory.create_narrator_model(section_number=3)
    with pytest.raises(StateError, match="Section number mismatch"):
        model_factory.create_game_state(
            game_id="test_game",
            session_id="test_session",
            section_number=2,
            narrative=narrator_model_wrong
        )

def test_game_state_update(model_factory):
    """Test updating GameState fields."""
    # Create initial state
    initial_state = model_factory.create_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        narrative=model_factory.create_narrator_model(section_number=1)
    )
    
    # Update with new section and narrative
    updated_state = initial_state.model_copy(update={
        "section_number": 2,
        "narrative": model_factory.create_narrator_model(section_number=2)
    })
    
    # Verify updates
    assert updated_state.section_number == 2
    assert updated_state.narrative.section_number == 2
    assert updated_state.game_id == initial_state.game_id
    assert updated_state.session_id == initial_state.session_id

def test_game_state_validation_error(model_factory):
    """Test validation errors in GameState."""
    # Create models with mismatched section numbers
    narrator_model = model_factory.create_narrator_model(section_number=1)
    
    with pytest.raises(StateError, match="Section number mismatch"):
        model_factory.create_game_state(
            game_id="test_game",
            session_id="test_session",
            section_number=3,  # Mismatch with narrator model
            narrative=narrator_model
        )

def test_game_state_serialization(model_factory):
    """Test serialization of GameState."""
    # Create state with all fields
    state = model_factory.create_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        character=model_factory.create_character(),
        narrative=model_factory.create_narrator_model(),
        rules=model_factory.create_rules_model(),
        decisions=model_factory.create_decision_model(),
        trace=model_factory.create_trace_model(),
        player_input="test input"
    )
    
    # Serialize to dict
    state_dict = state.model_dump()
    
    # Verify all fields
    assert state_dict["game_id"] == "test_game"
    assert state_dict["session_id"] == "test_session"
    assert state_dict["section_number"] == 1
    assert state_dict["player_input"] == "test input"
    assert isinstance(state_dict["character"], dict)
    assert isinstance(state_dict["narrative"], dict)
    assert isinstance(state_dict["rules"], dict)
    assert isinstance(state_dict["decisions"], dict)
    assert isinstance(state_dict["trace"], dict)

def test_game_state_with_player_input(model_factory):
    """Test GameState with player input."""
    # Create state with player input
    state = model_factory.create_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        player_input="examine room"
    )
    assert state.player_input == "examine room"
    
    # Update player input
    updated_state = state.model_copy(update={"player_input": "go north"})
    assert updated_state.player_input == "go north"
    assert state.player_input == "examine room"  # Original unchanged

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
    assert state.decisions is None
    assert state.trace is None
    assert state.player_input is None
    
    # Add optional field
    updated_state = state.model_copy(update={
        "narrative": model_factory.create_narrator_model(section_number=1)
    })
    assert updated_state.narrative is not None
    assert updated_state.rules is None  # Other fields still None
