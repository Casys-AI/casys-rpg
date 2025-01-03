"""
Point d'entrée principal de l'application Casys RPG.
"""
import os
import sys
from pathlib import Path

# Add project root to PYTHONPATH
project_dir = Path(__file__).parent
if str(project_dir) not in sys.path:
    sys.path.append(str(project_dir))

from config.logging_config import setup_logging, get_logger, log_env_variables
from dotenv import load_dotenv, find_dotenv

# Configure logging first
setup_logging()
logger = get_logger(__name__)

# Import app after logging setup
from api.app import app

if __name__ == "__main__":
    import uvicorn
    
    # Load environment variables
    dotenv_path = find_dotenv()
    logger.debug(f"Loading .env from: {dotenv_path}")
    load_dotenv(dotenv_path)
    
    # Get configuration from environment
    host = os.getenv("CASYS_HOST", "127.0.0.1")
    port = int(os.getenv("CASYS_PORT", "8001"))
    reload = os.getenv("CASYS_RELOAD", "True").lower() == "true"
    
    # Log environment variables
    log_env_variables()
    
    logger.info(f"Démarrage du serveur sur {host}:{port}")
    
    # Start server
    try:
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            log_level=os.getenv("LOG_LEVEL", "info").lower()
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
