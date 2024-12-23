"""Tests for feedback model."""
import pytest
from datetime import datetime
from models.feedback_model import FeedbackRequest, FeedbackType
from models.game_state import GameState
from models.trace_model import TraceModel

def test_feedback_request_creation():
    """Test creation of feedback request with minimal required fields."""
    game_state = GameState(
        session_id="test_session",
        section_number=1
    )
    feedback = FeedbackRequest(
        content="Test feedback",
        current_section=1,
        game_state=game_state,
        session_id="test_session"
    )
    
    assert feedback.content == "Test feedback"
    assert feedback.current_section == 1
    assert feedback.feedback_type == FeedbackType.COMMENT  # Default value
    assert isinstance(feedback.timestamp, datetime)
    assert feedback.user_id is None  # Optional field
    assert feedback.session_id == "test_session"
    assert isinstance(feedback.game_state, GameState)
    assert isinstance(feedback.trace_history, list)

def test_feedback_request_with_all_fields():
    """Test creation of feedback request with all fields populated."""
    game_state = GameState(
        session_id="test_session",
        section_number=1
    )
    trace = TraceModel(
        game_id="test_game",
        session_id="test_session"
    )
    
    custom_time = datetime(2024, 1, 1, 12, 0)
    feedback = FeedbackRequest(
        content="Detailed feedback",
        current_section=1,
        game_state=game_state,
        session_id="test_session",
        feedback_type=FeedbackType.BUG,
        user_id="test_user",
        timestamp=custom_time,
        trace_history=[trace]
    )
    
    assert feedback.content == "Detailed feedback"
    assert feedback.feedback_type == FeedbackType.BUG
    assert feedback.user_id == "test_user"
    assert feedback.timestamp == custom_time
    assert len(feedback.trace_history) == 1

def test_feedback_request_with_custom_timestamp():
    """Test creation of feedback request with custom timestamp."""
    game_state = GameState(
        session_id="test_session",
        section_number=1
    )
    custom_time = datetime(2024, 1, 1, 12, 0)
    
    feedback = FeedbackRequest(
        content="Time-specific feedback",
        current_section=1,
        game_state=game_state,
        session_id="test_session",
        timestamp=custom_time
    )
    
    assert feedback.timestamp == custom_time

def test_feedback_request_with_multiple_traces():
    """Test feedback request with multiple trace entries."""
    game_state = GameState(
        session_id="test_session",
        section_number=1
    )
    traces = [
        TraceModel(
            game_id=f"game_{i}",
            session_id="test_session"
        )
        for i in range(3)
    ]
    
    feedback = FeedbackRequest(
        content="Multi-trace feedback",
        current_section=1,
        game_state=game_state,
        session_id="test_session",
        trace_history=traces
    )
    
    assert len(feedback.trace_history) == 3
    for i, trace in enumerate(feedback.trace_history):
        assert trace.game_id == f"game_{i}"

def test_feedback_request_json_serialization():
    """Test that feedback request can be serialized to JSON."""
    game_state = GameState(
        session_id="test_session",
        section_number=1
    )
    feedback = FeedbackRequest(
        content="JSON test",
        current_section=1,
        game_state=game_state,
        session_id="test_session"
    )
    
    json_data = feedback.model_dump_json()
    assert "JSON test" in json_data
    assert "test_session" in json_data

def test_feedback_request_validation():
    """Test validation of feedback request fields."""
    game_state = GameState(
        session_id="test_session",
        section_number=1
    )
    
    # Test invalid feedback type
    with pytest.raises(ValueError):
        FeedbackRequest(
            content="Test",
            current_section=1,
            game_state=game_state,
            session_id="test_session",
            feedback_type="invalid_type"  # Invalid feedback type
        )
    
    # Test empty content
    with pytest.raises(ValueError):
        FeedbackRequest(
            content="   ",  # Just whitespace
            current_section=1,
            game_state=game_state,
            session_id="test_session"
        )
    
    # Test invalid section number
    with pytest.raises(ValueError):
        FeedbackRequest(
            content="Test",
            current_section=-1,  # Invalid section number
            game_state=game_state,
            session_id="test_session"
        )
        
    # Test empty session_id
    with pytest.raises(ValueError):
        FeedbackRequest(
            content="Test",
            current_section=1,
            game_state=game_state,
            session_id=""  # Empty session_id
        )
