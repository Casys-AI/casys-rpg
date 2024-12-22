"""
Narrator Manager Module
Handles section content loading and caching orchestration.
"""

from typing import Dict, Optional, Union
from datetime import datetime
import logging
from pathlib import Path

from config.storage_config import StorageConfig
from models.config_models import ConfigModel
from models.narrator_model import NarratorModel, SourceType
from models.errors_model import NarratorError
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
from agents.protocols.narrator_agent_protocol import NarratorAgentProtocol
from managers.protocols.narrator_manager_protocol import NarratorManagerProtocol

class NarratorManager(NarratorManagerProtocol):
    """Orchestrates section content loading, processing and caching."""
    
    def __init__(self, 
                 config: StorageConfig, 
                 cache_manager: CacheManagerProtocol):
        """Initialize NarratorManager.
        
        Args:
            config: Storage configuration
            cache_manager: Cache manager for content storage
        """
        self.config = config
        self.cache = cache_manager
        self.logger = logging.getLogger(__name__)

    def _content_to_markdown(self, model: NarratorModel) -> str:
        """Convert NarratorModel to markdown format."""
        return model.content

    def _markdown_to_content(self, content: str, section_number: int) -> Optional[NarratorModel]:
        """Parse markdown content to NarratorModel."""
        try:
            # Verify the content starts with the correct section header
            lines = content.split('\n')
            if not lines or not lines[0].strip().startswith(f'# Section {section_number}'):
                self.logger.warning(f"Invalid section header for section {section_number}")
                return None

            return NarratorModel(
                section_number=section_number,
                content=content,
                source_type=SourceType.RAW,
                timestamp=datetime.now()
            )
        except Exception as e:
            self.logger.error(f"Error parsing markdown for section {section_number}: {str(e)}")
            return None

    async def get_section_content(self, section_number: int) -> Union[NarratorModel, NarratorError]:
        """Get processed section content, managing cache and processing.
        
        Args:
            section_number: Section number to retrieve
            
        Returns:
            Union[NarratorModel, NarratorError]: Processed section or error
        """
        try:
            # 1. Check cache first
            cached_content = await self.cache.get_cached_content(
                key=f"{section_number}",
                namespace="sections"
            )
            
            if cached_content:
                self.logger.info(f"Cache hit for section {section_number}")
                narrator_model = self._markdown_to_content(cached_content, section_number)
                if narrator_model:
                    narrator_model.source_type = SourceType.PROCESSED
                    return narrator_model
                    
            # 2. Get raw content if not in cache
            raw_content = await self.cache.load_raw_content(
                section_number=section_number,
                namespace="sections"
            )
            if not raw_content:
                self.logger.warning(f"Section {section_number} not found")
                return NarratorError(
                    section_number=section_number,
                    message=f"Section {section_number} not found"
                )

            # 3. Create narrator model
            narrator_model = NarratorModel(
                section_number=section_number,
                content=raw_content,
                source_type=SourceType.PROCESSED,
                timestamp=datetime.now()
            )
            
            # 4. Save to cache
            await self.save_section_content(narrator_model)
                
            return narrator_model

        except Exception as e:
            self.logger.error(f"Error processing section {section_number}: {str(e)}")
            return NarratorError(
                section_number=section_number,
                message=f"Error processing section: {str(e)}"
            )

    async def save_section_content(self, content: NarratorModel) -> Optional[NarratorError]:
        """Save section content to storage.
        
        Args:
            content: NarratorModel to save
            
        Returns:
            Optional[NarratorError]: Error if save failed, None if successful
        """
        try:
            # Ensure source type is PROCESSED
            content.source_type = SourceType.PROCESSED
            
            # Convert to markdown
            markdown_content = self._content_to_markdown(content)
            
            # Save to cache
            success = await self.cache.save_cached_content(
                key=f"{content.section_number}",
                namespace="sections",
                data=markdown_content
            )
            
            if not success:
                return NarratorError(
                    section_number=content.section_number,
                    message="Failed to save content to cache"
                )
                
            return None

        except Exception as e:
            self.logger.error(f"Error saving content: {str(e)}")
            return NarratorError(
                section_number=content.section_number,
                message=f"Error saving content: {str(e)}"
            )

    async def exists_raw_section(self, section_number: int) -> bool:
        """Check if raw section exists.
        
        Args:
            section_number: Section to check
            
        Returns:
            bool: True if exists
        """
        try:
            return await self.cache.exists_raw_content(section_number, "sections")
        except Exception as e:
            self.logger.error(f"Error checking section existence for section {section_number}: {str(e)}")
            return False

    async def get_raw_section_content(self, section_number: int) -> Optional[str]:
        """Get raw section content."""
        try:
            return await self.cache.load_raw_content(
                section_number=section_number,
                namespace="sections"
            )
        except Exception as e:
            self.logger.error(f"Error getting raw content for section {section_number}: {str(e)}")
            return None
