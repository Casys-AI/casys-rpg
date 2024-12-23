"""Logging configuration for the entire application."""
import os
import sys
from pathlib import Path
from loguru import logger
import logging

# Get log level from environment or use INFO as default
DEFAULT_LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

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
    """Configure logging for the entire application."""
    # Remove default handler
    logger.remove()
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Add console handler with custom format
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=DEFAULT_LOG_LEVEL,
        enqueue=True,  # Thread-safe logging
        backtrace=True,  # Detailed error traces
        diagnose=True,  # Even more detailed error information
    )
    
    # Add file handler for errors
    logger.add(
        "logs/errors.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="1 day",  # Create new file daily
        retention="7 days",  # Keep logs for 7 days
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )
    
    # Add file handler for debug logs
    logger.add(
        "logs/debug.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="1 day",
        retention="3 days",
        enqueue=True,
    )
    
    # Configure uvicorn logging
    logging.getLogger("uvicorn").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    
    # Log startup information
    logger.info("Logging system initialized")
    logger.debug(f"Log level set to: {DEFAULT_LOG_LEVEL}")

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
