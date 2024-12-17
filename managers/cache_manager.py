"""
Cache Manager Module
Handles caching of game sections and related data.
"""

from typing import Dict, Optional, Any
import logging
from logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger('cache_manager')

class CacheManager:
    """
    Manages caching of game sections and related data.
    """
    
    def __init__(self):
        """Initialize CacheManager with an empty cache."""
        self._section_cache: Dict[int, Any] = {}
        
    def check_section_cache(self, section_number: int) -> bool:
        """
        Check if a section is cached.
        
        Args:
            section_number: Section number to check
            
        Returns:
            bool: True if section is cached, False otherwise
        """
        return section_number in self._section_cache
        
    def get_section(self, section_number: int) -> Optional[Any]:
        """
        Get a section from cache.
        
        Args:
            section_number: Section number to retrieve
            
        Returns:
            Optional[Any]: Cached section data if exists, None otherwise
        """
        try:
            return self._section_cache.get(section_number)
        except Exception as e:
            logger.error(f"Error getting section from cache: {str(e)}")
            return None
            
    def cache_section(self, section_number: int, data: Any) -> None:
        """
        Cache section data.
        
        Args:
            section_number: Section number to cache
            data: Data to cache
        """
        try:
            self._section_cache[section_number] = data
        except Exception as e:
            logger.error(f"Error caching section: {str(e)}")
            raise
            
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._section_cache.clear()

    async def get_section_content(self, section_number: int) -> Optional[str]:
        """
        Get the content of a section from cache or file.
        
        Args:
            section_number: Section number to retrieve
            
        Returns:
            Optional[str]: Section content if exists, None otherwise
        """
        try:
            logger.info(f"Récupération du contenu de la section {section_number}")
            
            # D'abord vérifier le cache
            if self.check_section_cache(section_number):
                logger.info("Contenu trouvé dans le cache")
                return self.get_section(section_number)
            
            # Sinon, charger depuis le fichier
            import os
            from pathlib import Path
            
            # Construire le chemin du fichier
            base_dir = Path(__file__).parent.parent
            section_file = base_dir / "data" / "sections" / f"section_{section_number}.txt"
            
            # Vérifier si le fichier existe
            if not os.path.exists(section_file):
                logger.warning(f"Fichier de section non trouvé: {section_file}")
                return None
                
            # Lire le contenu
            logger.info(f"Lecture du fichier: {section_file}")
            with open(section_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            # Mettre en cache
            self.cache_section(section_number, content)
            
            return content
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du contenu: {str(e)}", exc_info=True)
            return None
