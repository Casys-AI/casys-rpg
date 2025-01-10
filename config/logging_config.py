"""Logging configuration for the entire application."""
import os
import sys
from pathlib import Path
from loguru import logger
import logging

# Get log level from environment or use INFO as default
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

# Intercept standard logging
class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logging():
    """Configure logging with rotation and backup count."""
    try:
        logger.info(f"Configuring logging with level: {LOG_LEVEL}")
        
        # Ensure logs directory exists
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure loguru with rotation
        config = {
            "handlers": [
                {
                    "sink": sys.stdout,
                    "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                    "level": "INFO",
                    "backtrace": True,
                    "diagnose": True
                },
                {
                    "sink": "logs/debug.log",
                    "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                    "level": "DEBUG",
                    "rotation": "5 minutes",  # Rotation toutes les 5 minutes
                    "retention": 0,           # Ne garde pas les vieux fichiers
                    "mode": "w",             # Mode écriture (écrase le fichier)
                    "enqueue": True          # Thread-safe writing
                },
                {
                    "sink": "logs/errors.log",
                    "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                    "level": "ERROR",        # Seulement les erreurs
                    "rotation": "1 MB",      # Rotation basée sur la taille
                    "retention": 0,          # Ne garde pas les vieux fichiers
                    "mode": "w",            # Mode écriture (écrase le fichier)
                    "enqueue": True,        # Thread-safe writing
                    "backtrace": True,      # Stack trace complet
                    "diagnose": True        # Diagnostic amélioré
                }
            ]
        }
        
        # Remove default handler and add our configuration
        logger.remove()
        for handler in config["handlers"]:
            logger.add(**handler)
            
        logger.success("Logging configured successfully")
        
    except Exception as e:
        print(f"Error setting up logging: {str(e)}")
        raise

def get_logger(name: str):
    """Get a logger with the specified name.
    
    Args:
        name: The name of the logger to get
        
    Returns:
        A configured logger instance
    """
    return logger.bind(name=name)

def log_env_variables():
    """Log environment variables for debugging."""
    logger.debug("Environment variables:")
    env_vars = ["CASYS_HOST", "CASYS_PORT", "CASYS_RELOAD", "LOG_LEVEL"]
    for var in env_vars:
        logger.debug(f"{var}: {os.getenv(var)}")
