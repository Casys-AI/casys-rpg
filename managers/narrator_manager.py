"""
Narrator Manager Module
Handles game content and narrative elements.
"""

from typing import Dict, Optional, Any, Union
from datetime import datetime
import logging
from pathlib import Path
from loguru import logger

from config.storage_config import StorageConfig
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
from managers.protocols.narrator_manager_protocol import NarratorManagerProtocol
from models.narrator_model import NarratorModel, SourceType
from models.errors_model import NarratorError

class NarratorManager(NarratorManagerProtocol):
    """Manages game content and narrative elements."""

    def __init__(self, config: StorageConfig, cache_manager: CacheManagerProtocol):
        """Initialize NarratorManager.
        
        Args:
            config: Storage configuration
            cache_manager: Cache manager instance
        """
        logger.info("Initializing NarratorManager")
        self.config = config
        self.cache = cache_manager
        self.logger = logging.getLogger(__name__)
        logger.debug("NarratorManager initialized with config: %s", config.__class__.__name__)

    async def get_cached_content(self, section_number: int) -> Optional[NarratorModel]:
        """Get content from cache only."""
        try:
            logger.info(f"Getting cached content for section {section_number}")
            
            content = await self.cache.get_cached_content(
                key=f"section_{section_number}",
                namespace="cached_sections"
            )
            if not content:
                logger.debug(f"No content found in cache for section {section_number}")
                return None
                
            # Parse le markdown en NarratorModel
            model = self._markdown_to_narrator(content, section_number)
            if model:
                logger.debug(f"Successfully parsed cached content for section {section_number}")
                return model
                
            logger.warning(f"Failed to parse cached content for section {section_number}")
            return None
            
        except KeyError:
            logger.warning(f"Invalid namespace for section {section_number}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached content: {str(e)}")
            return None

    async def get_raw_content(self, section_number: int) -> Union[str, NarratorError]:
        """Get raw content from storage."""
        try:
            logger.info(f"Getting raw content for section {section_number}")
            
            exists = await self.cache.exists_raw_content(
                key=str(section_number),
                namespace="sections"
            )
            logger.debug(f"Raw content exists check: {exists}")
            
            if not exists:
                logger.warning(f"No raw content found for section {section_number}")
                return NarratorError(
                    section_number=section_number,
                    message=f"No raw content found for section {section_number}"
                )
                
            content = await self.cache.load_raw_content(
                key=str(section_number),
                namespace="sections"
            )
            logger.debug(f"Raw content loaded: {content is not None}")
            
            if content:
                logger.debug(f"Found raw content for section {section_number}")
                return content
                
            logger.warning(f"Failed to load raw content for section {section_number}")
            return NarratorError(
                section_number=section_number,
                message=f"Failed to load raw content for section {section_number}"
            )
            
        except KeyError:
            logger.error(f"Invalid namespace for section {section_number}")
            return NarratorError(
                section_number=section_number,
                message="Invalid namespace configuration"
            )
        except Exception as e:
            logger.error(f"Error loading raw content: {str(e)}", exc_info=True)
            return NarratorError(
                section_number=section_number,
                message=f"Error loading raw content: {str(e)}"
            )

    async def save_content(self, model: NarratorModel) -> Union[NarratorModel, NarratorError]:
        """Save content to cache."""
        try:
            logger.info(f"Saving content for section {model.section_number}")
            
            # Convertir en markdown simple
            markdown_content = self._narrator_to_markdown(model)
            if not markdown_content:
                logger.error(f"Failed to convert content to markdown for section {model.section_number}")
                return NarratorError(
                    section_number=model.section_number,
                    message="Failed to convert content to markdown"
                )
            
            await self.cache.save_cached_content(
                key=f"section_{model.section_number}",
                namespace="cached_sections",
                data=markdown_content
            )
            
            logger.debug(f"Content saved successfully for section {model.section_number}")
            return model
            
        except KeyError:
            logger.error(f"Invalid namespace for section {model.section_number}")
            return NarratorError(
                section_number=model.section_number,
                message="Invalid namespace configuration"
            )
        except Exception as e:
            logger.error(f"Error saving content: {str(e)}")
            return NarratorError(
                section_number=model.section_number,
                message=f"Error saving content: {str(e)}"
            )

    def _markdown_to_narrator(self, content: str, section_number: int) -> Optional[NarratorModel]:
        """Convert markdown content to NarratorModel.
        
        Args:
            content: Raw markdown content
            section_number: Section number
            
        Returns:
            Optional[NarratorModel]: Parsed model if successful, None otherwise
        """
        try:
            logger.debug(f"Converting markdown to NarratorModel for section {section_number}")
            
            # Parse le contenu markdown
            lines = content.strip().split('\n')
            if not lines:
                logger.error("Content is empty")
                return None
                
            # Vérifie le header de section
            if not lines[0].strip().startswith(f'# Section {section_number}'):
                logger.error(f"Invalid section header for section {section_number}")
                return None
                
            # Le contenu est tout ce qui suit le header
            content = '\n'.join(lines[1:]).strip()
            if not content:
                logger.error("Content section is empty")
                return None
                
            # Create NarratorModel
            return NarratorModel(
                section_number=section_number,
                content=content,
                source_type=SourceType.RAW,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error converting markdown to NarratorModel: {str(e)}")
            return None

    def _narrator_to_markdown(self, model: NarratorModel) -> str:
        """Convert NarratorModel to markdown format.
        
        Args:
            model: NarratorModel to convert
            
        Returns:
            str: Markdown formatted content
        """
        try:
            logger.debug(f"Converting NarratorModel to markdown for section {model.section_number}")
            
            # Format simple : header + content
            return f"# Section {model.section_number}\n\n{model.content.strip()}"
            
        except Exception as e:
            logger.error(f"Error converting NarratorModel to markdown: {str(e)}")
            return ""

    async def exists_raw_section(self, section_number: int) -> bool:
        """Check if raw section exists."""
        try:
            logger.debug(f"Checking if section {section_number} exists")
            exists = await self.cache.exists_raw_content(
                key=str(section_number),
                namespace="sections"
            )
            logger.debug(f"Section {section_number} exists: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking section {section_number} existence: {str(e)}")
            return False

    async def get_raw_section_content(self, section_number: int) -> Optional[str]:
        """Get raw section content."""
        try:
            logger.debug(f"Getting raw content for section {section_number}")
            return await self.cache.load_raw_content(
                key=str(section_number),
                namespace="sections"
            )
        except Exception as e:
            logger.error(f"Error getting raw content for section {section_number}: {str(e)}")
            logger.error(f"Error getting raw content for section {section_number}: {str(e)}", exc_info=True)
            return None

    async def exists_section(self, section_number: int) -> bool:
        """Check if a section exists."""
        try:
            logger.debug(f"Checking if section {section_number} exists")
            exists = await self.cache.exists_raw_content(
                key=str(section_number),
                namespace="sections"
            )
            logger.debug(f"Section {section_number} exists: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking section {section_number} existence: {str(e)}")
            logger.error(f"Error checking section {section_number} existence: {str(e)}", exc_info=True)
            return False
