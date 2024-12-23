"""Tests for the trace model."""
import pytest
from datetime import datetime
from models.trace_model import TraceModel, TraceAction, ActionType

def test_add_action():
    """Test adding a single action to the trace."""
    # Create a new trace model with required fields
    trace = TraceModel(
        game_id="test_game",
        session_id="test_session"
    )
    
    # Create a test action
    action_data = {
        "section": 1,
        "action_type": ActionType.USER_INPUT,
        "details": {"input": "go north"}
    }
    
    # Add the action
    trace.add_action(action_data)
    
    # Verify the action was added correctly
    assert len(trace.history) == 1
    added_action = trace.history[0]
    assert added_action.section == 1
    assert added_action.action_type == ActionType.USER_INPUT
    assert added_action.details["input"] == "go north"

def test_add_multiple_actions():
    """Test adding multiple actions to the trace."""
    trace = TraceModel(
        game_id="test_game",
        session_id="test_session"
    )
    
    # Add multiple actions
    actions = [
        {
            "section": 1,
            "action_type": ActionType.USER_INPUT,
            "details": {"input": "examine room"}
        },
        {
            "section": 2,
            "action_type": ActionType.DICE_ROLL,
            "details": {
                "roll_result": 6,
                "roll_type": "combat",
                "modifier": 2
            }
        }
    ]
    
    for action in actions:
        trace.add_action(action)
    
    # Verify all actions were added
    assert len(trace.history) == 2
    assert trace.history[0].section == 1
    assert trace.history[1].section == 2
    assert trace.history[1].details["roll_result"] == 6

def test_add_action_with_trace_action_instance():
    """Test adding a TraceAction instance directly."""
    trace = TraceModel(
        game_id="test_game",
        session_id="test_session"
    )
    
    action = TraceAction(
        section=1,
        action_type=ActionType.USER_INPUT,
        details={"input": "look"}
    )
    
    trace.add_action(action.model_dump())
    assert len(trace.history) == 1
    assert trace.history[0].section == 1

def test_add_action_maintains_immutability():
    """Test that adding actions maintains immutability of history."""
    trace = TraceModel(
        game_id="test_game",
        session_id="test_session"
    )
    
    # Initial action
    action1 = {
        "section": 1,
        "action_type": ActionType.USER_INPUT,
        "details": {"input": "start"}
    }
    trace.add_action(action1)
    
    # Store the first action
    first_action = trace.history[0]
    
    # Add another action
    action2 = {
        "section": 2,
        "action_type": ActionType.USER_INPUT,
        "details": {"input": "continue"}
    }
    trace.add_action(action2)
    
    # Verify first action hasn't changed
    assert trace.history[0] == first_action
    assert len(trace.history) == 2

def test_add_action_with_empty_history():
    """Test adding action when history is empty."""
    trace = TraceModel(
        game_id="test_game",
        session_id="test_session"
    )
    
    assert len(trace.history) == 0
    
    action = {
        "section": 1,
        "action_type": ActionType.USER_INPUT,
        "details": {"input": "start"}
    }
    trace.add_action(action)
    
    assert len(trace.history) == 1

def test_add_action_validates_data():
    """Test that action data is properly validated."""
    trace = TraceModel(
        game_id="test_game",
        session_id="test_session"
    )
    
    # Test with invalid section number
    with pytest.raises(ValueError):
        trace.add_action({
            "section": -1,  # Invalid: must be positive
            "action_type": ActionType.USER_INPUT,
            "details": {"input": "test"}
        })
        
    # Test dice roll without roll_result
    with pytest.raises(ValueError, match="Dice roll actions must include 'roll_result' in details"):
        trace.add_action({
            "section": 1,
            "action_type": ActionType.DICE_ROLL,
            "details": {"modifier": 2}  # Missing roll_result
        })
        
    # Test user input without input field
    with pytest.raises(ValueError, match="User input actions must include 'input' in details"):
        trace.add_action({
            "section": 1,
            "action_type": ActionType.USER_INPUT,
            "details": {}  # Missing input
        })

def test_model_validation():
    """Test model validation rules."""
    # Test with empty session_id
    with pytest.raises(ValueError):
        TraceModel(
            game_id="test_game",
            session_id=""  # Invalid: cannot be empty
        )
    
    # Test with invalid section_number
    with pytest.raises(ValueError):
        TraceModel(
            game_id="test_game",
            session_id="test_session",
            section_number=-1  # Invalid: must be >= 0
        )
