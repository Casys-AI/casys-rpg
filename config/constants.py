"""Global constants for the game engine."""
from enum import Enum
from pathlib import Path

# Directory paths
DATA_DIR = Path("data")
SECTIONS_DIR = DATA_DIR / "sections"
RULES_DIR = DATA_DIR / "rules"
CACHE_DIR = DATA_DIR / "sections/cache"
TRACE_DIR = DATA_DIR / "trace"
FEEDBACK_DIR = DATA_DIR / "feedback"

class ModelType(str, Enum):
    """Available LLM models."""
    NARRATOR = "gpt-4o-mini"
    RULES = "gpt-4o-mini"
    DECISION = "gpt-4o-mini"
    TRACE = "gpt-4o-mini"

class GameState(str, Enum):
    """Game states."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"

# Default configurations
DEFAULT_TEMPERATURE = 0.7
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30

# Cache settings
CACHE_ENABLED = True
CACHE_TTL = 3600  # 1 hour

# Logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_LEVEL = "INFO"
