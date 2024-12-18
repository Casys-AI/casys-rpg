"""Logging configuration for the entire application."""
import logging.config
import os
from config.constants import LOG_FORMAT

# Get log level from environment or use INFO as default
DEFAULT_LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': LOG_FORMAT
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console'],
            'level': DEFAULT_LOG_LEVEL,
            'propagate': True
        },
        'api': {  # API specific logger
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False
        },
        'agents': {  # All agents logger
            'handlers': ['console'],
            'level': DEFAULT_LOG_LEVEL,
            'propagate': False
        },
        'story_graph': {  # StoryGraph logger
            'handlers': ['console'],
            'level': DEFAULT_LOG_LEVEL,
            'propagate': False
        },
        'openai': {  # OpenAI calls logger
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False
        },
        'httpx': {  # HTTP requests logger
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False
        },
        'httpcore': {  # HTTP core logger
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False
        }
    }
}

def setup_logging():
    """Configure logging for the entire application."""
    logging.config.dictConfig(LOGGING_CONFIG)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.
    
    Args:
        name: The name of the logger to get
        
    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)
