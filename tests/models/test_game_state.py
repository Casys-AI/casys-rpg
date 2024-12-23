"""Tests for game state models."""
import pytest
from datetime import datetime
from models.game_state import GameState, GameStateInput, GameStateOutput
from models.decision_model import DiceResult, DecisionModel
from models.character_model import CharacterModel
from models.narrator_model import NarratorModel, SourceType as NarratorSourceType
from models.rules_model import RulesModel, DiceType, SourceType as RulesSourceType
from models.trace_model import TraceModel, ActionType

def test_game_state_input_creation():
    """Test creation of game state input."""
    input_state = GameStateInput(section_number=1)
    
    assert input_state.section_number == 1
    assert input_state.player_input is None
    assert isinstance(input_state.effects, dict)
    assert isinstance(input_state.flags, dict)

def test_game_state_output_creation():
    """Test creation of game state output."""
    output_state = GameStateOutput()
    
    assert output_state.narrative is None
    assert output_state.rules is None
    assert output_state.trace is None
    assert output_state.character is None
    assert output_state.dice_roll is None
    assert output_state.decision is None
    assert output_state.error is None

def test_game_state_creation():
    """Test creation of complete game state."""
    game_state = GameState(section_number=1)
    
    assert game_state.section_number == 1
    assert game_state.source == RulesSourceType.RAW
    assert isinstance(game_state.last_update, datetime)
    assert game_state.narrative_content is None
    assert game_state.current_rules is None
    assert game_state.current_decision is None

def test_game_state_with_components():
    """Test game state with all components."""
    section_number = 1
    narrator = NarratorModel(section_number=section_number)
    rules = RulesModel(section_number=section_number)
    trace = TraceModel(
        game_id="test_game",
        session_id="test",
        section_number=section_number,
        history=[],
        current_action=ActionType.USER_INPUT
    )
    character = CharacterModel()
    dice_roll = DiceResult(type=DiceType.COMBAT, value=4)
    decision = DecisionModel(section_number=section_number)
    
    game_state = GameState(
        section_number=section_number,
        narrative=narrator,
        rules=rules,
        trace=trace,
        character=character,
        dice_roll=dice_roll,
        decision=decision
    )
    
    assert game_state.narrative == narrator
    assert game_state.rules == rules
    assert game_state.trace == trace
    assert game_state.character == character
    assert game_state.dice_roll == dice_roll
    assert game_state.decision == decision
    
    # Verify section number consistency
    assert game_state.narrative.section_number == section_number
    assert game_state.rules.section_number == section_number
    assert game_state.trace.section_number == section_number
    assert game_state.decision.section_number == section_number

def test_game_state_validation():
    """Test game state validation."""
    # Test invalid section number
    with pytest.raises(ValueError):
        GameState(section_number=0)
    
    # Test section number mismatch
    with pytest.raises(ValueError):
        GameState(
            section_number=1,
            narrative=NarratorModel(section_number=2)
        )
    
    with pytest.raises(ValueError):
        GameState(
            section_number=1,
            rules=RulesModel(section_number=2)
        )

def test_game_state_with_player_input():
    """Test game state with player input."""
    game_state = GameState(
        section_number=1,
        player_input="go north"
    )
    
    assert game_state.player_input == "go north"

def test_game_state_with_effects():
    """Test game state with effects."""
    effects = {
        "health_boost": 10,
        "experience_gain": 100
    }
    game_state = GameState(
        section_number=1,
        effects=effects
    )
    
    assert game_state.effects == effects

def test_game_state_with_flags():
    """Test game state with flags."""
    flags = {
        "has_key": True,
        "door_unlocked": False
    }
    game_state = GameState(
        section_number=1,
        flags=flags
    )
    
    assert game_state.flags == flags

def test_game_state_json_serialization():
    """Test JSON serialization of game state."""
    section_number = 1
    game_state = GameState(
        section_number=section_number,
        player_input="test input",
        narrative=NarratorModel(section_number=section_number),
        rules=RulesModel(section_number=section_number),
        trace=TraceModel(
            game_id="test_game",
            session_id="test",
            section_number=section_number,
            history=[],
            current_action=ActionType.USER_INPUT
        )
    )
    
    # Serialize to JSON
    json_data = game_state.model_dump_json()
    assert isinstance(json_data, str)
    
    # Convert to dict for easier testing
    import json
    data_dict = json.loads(json_data)
    
    # Check key elements
    assert data_dict["section_number"] == section_number
    assert data_dict["player_input"] == "test input"
    assert data_dict["trace"]["session_id"] == "test"
    assert isinstance(data_dict["last_update"], str)  # Should be ISO format string

def test_game_state_datetime_handling():
    """Test datetime handling in game state."""
    from datetime import datetime, timezone
    custom_time = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    
    game_state = GameState(
        section_number=1,
        last_update=custom_time
    )
    
    # Test datetime serialization
    json_data = game_state.model_dump_json()
    import json
    data = json.loads(json_data)
    assert data["last_update"] == custom_time.isoformat()

def test_game_state_error_handling():
    """Test error handling in game state."""
    error_msg = "Test error"
    game_state = GameState(
        section_number=1,
        error=error_msg
    )
    
    assert game_state.error == error_msg
