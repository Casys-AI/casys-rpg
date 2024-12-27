"""
Custom error classes for the game.
"""

class GameError(Exception):
    """Base class for game-related errors."""
    def __init__(self, message: str = "", **kwargs):
        super().__init__(message)
        self.message = message
        for key, value in kwargs.items():
            setattr(self, key, value)

class CharacterError(GameError):
    """Error related to character operations."""
    def __init__(self, message: str = "", **kwargs):
        super().__init__(message, **kwargs)

class RulesError(GameError):
    """Error related to game rules."""
    def __init__(self, message: str = "", **kwargs):
        super().__init__(message, **kwargs)

class StateError(GameError):
    """Error related to game state."""
    def __init__(self, message: str = "", **kwargs):
        super().__init__(message, **kwargs)

class CacheError(GameError):
    """Error related to cache operations."""
    def __init__(self, message: str = "", **kwargs):
        super().__init__(message, **kwargs)

class FileSystemError(GameError):
    """Error related to file system operations."""
    def __init__(self, message: str = "", **kwargs):
        super().__init__(message, **kwargs)

class NarratorError(GameError):
    """Error related to narrative operations."""
    def __init__(self, message: str = "", **kwargs):
        super().__init__(message, **kwargs)

class DecisionError(GameError):
    """Error related to decision operations."""
    def __init__(self, message: str = "", **kwargs):
        super().__init__(message, **kwargs)

class TraceError(GameError):
    """Error related to trace operations."""
    def __init__(self, message: str = "", **kwargs):
        super().__init__(message, **kwargs)

class AgentError(GameError):
    """Error related to agent operations."""
    def __init__(self, message: str = "", **kwargs):
        super().__init__(message, **kwargs)

class ConfigError(GameError):
    """Error related to configuration operations."""
    def __init__(self, message: str = "", **kwargs):
        super().__init__(message, **kwargs)

class StorageError(GameError):
    """Error related to storage operations."""
    def __init__(self, message: str = "", **kwargs):
        super().__init__(message, **kwargs)

class WorkflowError(GameError):
    """Error related to workflow operations and transitions."""
    def __init__(self, message: str = "", **kwargs):
        super().__init__(message, **kwargs)

class AuthorError(GameError):
    """Error related to author operations."""
    def __init__(self, message: str = "", **kwargs):
        super().__init__(message, **kwargs)
