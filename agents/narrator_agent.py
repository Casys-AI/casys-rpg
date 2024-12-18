"""NarratorAgent Module
Handles reading and presenting game sections.
"""

from typing import Dict, Optional, AsyncGenerator, Any
from datetime import datetime
from pydantic import Field, ValidationError, BaseModel
from langchain_core.messages import SystemMessage, HumanMessage
import re

from agents.base_agent import BaseAgent
from models.game_state import GameState
from models.narrator_model import NarratorModel, SourceType
from managers.cache_manager import CacheManager
from config.agent_config import NarratorConfig
from config.logging_config import get_logger
from agents.protocols import NarratorAgentProtocol

logger = get_logger('narrator_agent')

class NarratorAgent(BaseAgent, NarratorAgentProtocol):
    """Agent responsable de la lecture et présentation des sections."""
    
    config: NarratorConfig = Field(default_factory=NarratorConfig)
    current_section: int = Field(default=1, description="Current section number")

    def __init__(self, config: NarratorConfig, cache_manager: CacheManager):
        """Initialize NarratorAgent.
        
        Args:
            config: Configuration for the agent
            cache_manager: Cache manager instance
        """
        super().__init__(config=config, cache_manager=cache_manager)
        self.current_section = 1
        self.logger = logger

    async def _read_section(self, section_number: int) -> NarratorModel:
        """Lit une section du livre.
        
        Args:
            section_number: Numéro de la section à lire
            
        Returns:
            NarratorModel: Section lue
        """
        try:
            # Try to get from cache first if source is "cache"
            cached_content = self.cache_manager.get_section_from_cache(section_number)
            if cached_content and isinstance(cached_content, NarratorModel):
                self.logger.info(f"[NarratorAgent] Section {section_number} trouvée en cache")
                return cached_content

            # Load raw content from file
            raw_content = self.cache_manager.load_raw_section_content(section_number)
            if not raw_content:
                self.logger.error(f"[NarratorAgent] Section {section_number} non trouvée")
                return NarratorModel(
                    section_number=section_number,
                    content="",
                    source_type=SourceType.RAW,
                    error="Section not found"
                )
                
            # Format content with LLM
            formatted_content = await self._format_content(raw_content)
            
            # Create and save section content
            section_content = NarratorModel(
                section_number=section_number,
                content=formatted_content,
                source_type=SourceType.RAW
            )
            
            # Save to cache
            self.cache_manager.save_section_to_cache(section_number, section_content)
            
            return section_content
            
        except Exception as e:
            self.logger.error(f"[NarratorAgent] Error reading section {section_number}: {str(e)}")
            return NarratorModel(
                section_number=section_number,
                content="",
                source_type=SourceType.RAW,
                error=f"Error reading section: {str(e)}"
            )

    async def _format_content(self, content: str) -> str:
        """Formate le contenu avec le LLM et Markdown.
        
        Args:
            content: Contenu brut à formater
            
        Returns:
            str: Contenu formaté
        """
        try:
            messages = [
                SystemMessage(content=self.config.system_message),
                HumanMessage(content=content)
            ]
            
            # Call LLM for formatting
            response = await self.config.llm.ainvoke(messages)
            
            if not response or not response.content:
                raise ValueError("Empty response from LLM")
                
            return response.content
            
        except Exception as e:
            self.logger.error(f"[NarratorAgent] Erreur formatage contenu: {e}")
            return content  # Return raw content if formatting fails

    async def format_content(self, content: str) -> str:
        """Format the content using the LLM.
        
        Args:
            content: Raw content to format
            
        Returns:
            str: Formatted content
        """
        return await self._format_content(content)

    async def ainvoke(self, input_data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Invoque l'agent narrateur.
        
        Args:
            input_data: Données d'entrée contenant l'état du jeu
            
        Yields:
            Dict[str, Any]: État du jeu mis à jour
        """
        try:
            # Validation des données d'entrée
            game_state = GameState(**input_data)
            
            # Lecture de la section
            content = await self._read_section(game_state.section_number)
            game_state.narrative = content
            
            # Retourne l'état sous forme de dictionnaire
            yield {"state": game_state.model_dump()}
            
        except Exception as e:
            self.logger.error(f"[NarratorAgent] Error in NarratorAgent.ainvoke: {str(e)}")
            raise
