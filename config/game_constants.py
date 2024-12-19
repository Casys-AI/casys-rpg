"""Game-wide constants and configuration values."""
from enum import Enum, auto
from typing import Dict, Any

class GameMode(str, Enum):
    """Game operation modes."""
    NORMAL = "normal"
    DEBUG = "debug"
    TEST = "test"

class GameState(str, Enum):
    """Game state enumeration."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    FINISHED = "finished"

class ModelType(str, Enum):
    """LLM model types for different agents."""
    NARRATOR = "gpt-4o-mini"  # Default model for narrative generation
    RULES = "gpt-4o-mini"     # Model for rules interpretation
    DECISION = "gpt-4o-mini"  # Model for decision making
    TRACE = "gpt-4o-mini"     # Model for trace analysis

# Default configuration values
DEFAULT_CONFIG: Dict[str, Any] = {
    "mode": GameMode.NORMAL,
    "state": GameState.INITIALIZING,
    "max_retries": 3,
    "timeout_seconds": 30,
}

# Cache settings
CACHE_CONFIG = {
    "enabled": True,
    "max_size": 1000,
    "ttl_seconds": 3600,
}

# Error messages
ERROR_MESSAGES = {
    "initialization": "Failed to initialize game components",
    "state_transition": "Invalid state transition attempted",
    "agent_error": "Agent failed to process request",
    "timeout": "Operation timed out",
}

# Default temperature for LLM responses
DEFAULT_TEMPERATURE = 0.7
