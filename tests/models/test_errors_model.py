"""Tests for error models."""
import pytest
from models.errors_model import (
    GameError,
    CharacterError,
    RulesError,
    StateError,
    CacheError,
    FileSystemError,
    NarratorError,
    DecisionError,
    TraceError,
    AgentError,
    ConfigError,
    StorageError
)

def test_game_error_base():
    """Test base GameError functionality."""
    # Test basic error
    error = GameError("Test error")
    assert str(error) == "Test error"
    assert error.message == "Test error"
    
    # Test with additional attributes
    error = GameError("Test error", code=404, severity="high")
    assert error.code == 404
    assert error.severity == "high"

def test_character_error():
    """Test CharacterError functionality."""
    error = CharacterError(
        "Invalid character stats",
        stat="health",
        value=-10
    )
    assert isinstance(error, GameError)
    assert error.message == "Invalid character stats"
    assert error.stat == "health"
    assert error.value == -10

def test_rules_error():
    """Test RulesError functionality."""
    error = RulesError(
        "Invalid rule condition",
        section=5,
        condition="invalid_condition"
    )
    assert isinstance(error, GameError)
    assert error.section == 5
    assert error.condition == "invalid_condition"

def test_state_error():
    """Test StateError functionality."""
    error = StateError(
        "Invalid game state transition",
        from_state="combat",
        to_state="dialogue"
    )
    assert isinstance(error, GameError)
    assert error.from_state == "combat"
    assert error.to_state == "dialogue"

def test_cache_error():
    """Test CacheError functionality."""
    error = CacheError(
        "Cache miss",
        key="player_stats",
        cache_type="memory"
    )
    assert isinstance(error, GameError)
    assert error.key == "player_stats"
    assert error.cache_type == "memory"

def test_file_system_error():
    """Test FileSystemError functionality."""
    error = FileSystemError(
        "File not found",
        path="/game/saves/save1.json",
        operation="read"
    )
    assert isinstance(error, GameError)
    assert error.path == "/game/saves/save1.json"
    assert error.operation == "read"

def test_narrator_error():
    """Test NarratorError functionality."""
    error = NarratorError(
        "Invalid narrative sequence",
        section_id=3,
        narrative_type="dialogue"
    )
    assert isinstance(error, GameError)
    assert error.section_id == 3
    assert error.narrative_type == "dialogue"

def test_decision_error():
    """Test DecisionError functionality."""
    error = DecisionError(
        "Invalid decision option",
        option="fight",
        available_options=["run", "hide"]
    )
    assert isinstance(error, GameError)
    assert error.option == "fight"
    assert error.available_options == ["run", "hide"]

def test_trace_error():
    """Test TraceError functionality."""
    error = TraceError(
        "Invalid trace entry",
        entry_type="action",
        entry_id=123
    )
    assert isinstance(error, GameError)
    assert error.entry_type == "action"
    assert error.entry_id == 123

def test_agent_error():
    """Test AgentError functionality."""
    error = AgentError(
        "Agent initialization failed",
        agent_type="rules",
        reason="configuration missing"
    )
    assert isinstance(error, GameError)
    assert error.agent_type == "rules"
    assert error.reason == "configuration missing"

def test_config_error():
    """Test ConfigError functionality."""
    error = ConfigError(
        "Missing required configuration",
        missing_key="api_key",
        config_file="config.yaml"
    )
    assert isinstance(error, GameError)
    assert error.missing_key == "api_key"
    assert error.config_file == "config.yaml"

def test_storage_error():
    """Test StorageError functionality."""
    error = StorageError(
        "Storage operation failed",
        operation="save",
        storage_type="database"
    )
    assert isinstance(error, GameError)
    assert error.operation == "save"
    assert error.storage_type == "database"

def test_error_inheritance():
    """Test error class inheritance relationships."""
    errors = [
        CharacterError("test"),
        RulesError("test"),
        StateError("test"),
        CacheError("test"),
        FileSystemError("test"),
        NarratorError("test"),
        DecisionError("test"),
        TraceError("test"),
        AgentError("test"),
        ConfigError("test"),
        StorageError("test")
    ]
    
    for error in errors:
        assert isinstance(error, GameError)
        assert isinstance(error, Exception)
