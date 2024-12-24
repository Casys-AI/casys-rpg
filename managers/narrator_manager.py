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
        logger.debug("NarratorManager initialized with config: {}", config.__class__.__name__)

    async def get_cached_content(self, section_number: int) -> Optional[NarratorModel]:
        """Get content from cache only."""
        logger.info("Getting cached content for section {}", section_number)
        
        try:
            content = await self.cache.get_cached_data(
                key=f"section_{section_number}",
                namespace="sections"  # Utilise le namespace sections pour le cache
            )
            if not content:
                logger.debug("No content found in cache for section {}", section_number)
                return None
                
            model = self._markdown_to_narrator(content, section_number)
            if model:
                logger.debug("Successfully parsed cached content for section {}", section_number)
                return model
                
            logger.warning("Failed to parse cached content for section {}", section_number)
            return None
            
        except KeyError:
            logger.warning("Invalid namespace for section {}", section_number)
            return None
        except Exception as e:
            logger.error("Error retrieving cached content: {}", str(e))
            return None

    async def get_raw_content(self, section_number: int) -> Union[str, NarratorError]:
        """Get raw content from storage."""
        logger.info("Getting raw content for section {}", section_number)
        
        try:
            # Check in raw_content/sections/
            key = f"{section_number}"
            if not await self.cache.exists_raw_content(
                key=key,
                namespace="raw_content"  # Vérifie dans raw_content
            ):
                logger.warning("No raw content found for section {}", section_number)
                return NarratorError(
                    section_number=section_number,
                    message=f"No raw content found for section {section_number}"
                )
                
            content = await self.cache.load_raw_content(
                key=key,
                namespace="raw_content"  # Charge depuis raw_content
            )
            if content:
                logger.debug("Found raw content for section {}", section_number)
                return content
                
            logger.warning("Failed to load raw content for section {}", section_number)
            return NarratorError(
                section_number=section_number,
                message=f"Failed to load raw content for section {section_number}"
            )
            
        except KeyError:
            logger.error("Invalid namespace for section {}", section_number)
            return NarratorError(
                section_number=section_number,
                message="Invalid namespace configuration"
            )
        except Exception as e:
            logger.error("Error loading raw content: {}", str(e))
            return NarratorError(
                section_number=section_number,
                message=str(e)
            )


    async def save_content(self, model: NarratorModel) -> Union[NarratorModel, NarratorError]:
        """Save content to cache."""
        logger.info("Saving content for section {}", model.section_number)
        
        try:
            markdown_content = self._narrator_to_markdown(model)
            if not markdown_content:
                logger.error("Failed to convert content to markdown for section {}", model.section_number)
                return NarratorError(
                    section_number=model.section_number,
                    message="Failed to convert content to markdown"
                )
            
            await self.cache.save_cached_data(
                key=f"section_{model.section_number}",
                namespace="sections",  # Utilise le namespace sections pour le cache
                data=markdown_content
            )
            
            logger.debug("Content saved successfully for section {}", model.section_number)
            return model
            
        except KeyError:
            logger.error("Invalid namespace for section {}", model.section_number)
            return NarratorError(
                section_number=model.section_number,
                message="Invalid namespace configuration"
            )
        except Exception as e:
            logger.error("Error saving content: {}", str(e))
            return NarratorError(
                section_number=model.section_number,
                message=str(e)
            )

    def _markdown_to_narrator(self, content: str, section_number: int) -> Optional[NarratorModel]:
        """Convert markdown content to NarratorModel.
        
        Args:
            content: Raw markdown content
            section_number: Section number
            
        Returns:
            Optional[NarratorModel]: Parsed model if successful, None otherwise
        """
        logger.debug("Converting markdown to NarratorModel for section {}", section_number)
        
        lines = content.strip().split('\n')
        if not lines:
            logger.error("Content is empty")
            return None
            
        if not lines[0].strip().startswith(f'# Section {section_number}'):
            logger.error("Invalid section header for section {}", section_number)
            return None
            
        content = '\n'.join(lines[1:]).strip()
        if not content:
            logger.error("Content section is empty")
            return None
            
        return NarratorModel(
            section_number=section_number,
            content=content,
            source_type=SourceType.RAW,
            timestamp=datetime.now()
        )

    def _narrator_to_markdown(self, model: NarratorModel) -> str:
        """Convert NarratorModel to markdown format.
        
        Args:
            model: NarratorModel to convert
            
        Returns:
            str: Markdown formatted content
        """
        logger.debug("Converting NarratorModel to markdown for section {}", model.section_number)
        
        return model.content.strip()