"""Test trace model module."""
import pytest
from datetime import datetime
from models import TraceModel, ActionType, CharacterModel, CharacterStats, Inventory

@pytest.fixture
def sample_trace_model():
    """Create a sample trace model."""
    return TraceModel(
        game_id="test_game",
        session_id="test_session",
        section_number=1
    )

@pytest.fixture
def sample_character():
    """Create a sample character."""
    return CharacterModel(
        name="Test Character",
        stats=CharacterStats(SKILL=10, STAMINA=20, LUCK=5),
        inventory=Inventory(items={})
    )

def test_trace_model_creation(sample_trace_model):
    """Test creating a trace model."""
    assert sample_trace_model.game_id == "test_game"
    assert sample_trace_model.session_id == "test_session"
    assert sample_trace_model.section_number == 1
    assert isinstance(sample_trace_model.start_time, datetime)
    assert isinstance(sample_trace_model.history, list)
    assert len(sample_trace_model.history) == 0
    assert sample_trace_model.current_section is None
    assert sample_trace_model.current_rules is None
    assert sample_trace_model.character is None
    assert sample_trace_model.error is None

def test_add_action(sample_trace_model):
    """Test adding an action to the trace."""
    action = {
        "section": 1,
        "action_type": ActionType.USER_INPUT,
        "details": {"input": "test"}
    }
    sample_trace_model.add_action(action)
    
    assert len(sample_trace_model.history) == 1
    last_action = sample_trace_model.history[-1]
    assert last_action.section == 1
    assert last_action.action_type == ActionType.USER_INPUT
    assert last_action.details == {"input": "test"}
    assert isinstance(last_action.timestamp, datetime)

def test_update_character(sample_trace_model, sample_character):
    """Test updating character in trace."""
    sample_trace_model.update_character(sample_character)
    
    assert sample_trace_model.character == sample_character
    assert len(sample_trace_model.history) == 1
    last_action = sample_trace_model.history[-1]
    assert last_action.action_type == ActionType.CHARACTER_UPDATE
    assert last_action.details["character"] == sample_character.model_dump()

def test_trace_model_validation():
    """Test trace model validation."""
    # Test invalid section number
    with pytest.raises(ValueError):
        TraceModel(
            game_id="test_game",
            session_id="test_session",
            section_number=-1
        )
    
    # Test invalid game_id
    with pytest.raises(ValueError):
        TraceModel(
            game_id="",
            session_id="test_session",
            section_number=1
        )
    
    # Test invalid session_id
    with pytest.raises(ValueError):
        TraceModel(
            game_id="test_game",
            session_id="",
            section_number=1
        )

def test_error_state_validation(sample_trace_model):
    """Test error state validation."""
    # Set error state
    sample_trace_model.error = "Test error"
    
    # Should not allow setting current_section with error
    with pytest.raises(ValueError):
        sample_trace_model.current_section = "Test section"
    
    # Should not allow setting current_rules with error
    with pytest.raises(ValueError):
        sample_trace_model.current_rules = "Test rules"
