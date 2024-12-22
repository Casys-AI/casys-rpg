"""NarratorAgent Module
Handles content processing and formatting.
"""

from typing import Dict, Optional, AsyncGenerator, Any, Union
from datetime import datetime
import json
from pydantic import Field
from langchain_core.messages import SystemMessage, HumanMessage

from agents.base_agent import BaseAgent
from models.game_state import GameState
from models.narrator_model import NarratorModel, SourceType
from models.errors_model import NarratorError
from config.agents.narrator_agent_config import NarratorAgentConfig
from config.logging_config import get_logger
from agents.protocols import NarratorAgentProtocol
from managers.protocols.narrator_manager_protocol import NarratorManagerProtocol

logger = get_logger('narrator_agent')

class NarratorAgent(BaseAgent, NarratorAgentProtocol):
    """Agent responsable du traitement et de la présentation du contenu."""
    
    config: NarratorAgentConfig = Field(default_factory=lambda: NarratorAgentConfig())

    def __init__(self, config: NarratorAgentConfig, narrator_manager: NarratorManagerProtocol):
        """Initialize NarratorAgent.
        
        Args:
            config: Configuration for the agent
            narrator_manager: Narrator manager instance
        """
        super().__init__(config=config)
        self.narrator_manager = narrator_manager
        self.logger = logger

    async def process_section(self, section_number: int, raw_content: Optional[str] = None) -> Union[NarratorModel, NarratorError]:
        """Process and format a section.
        
        Args:
            section_number: Section number to process
            raw_content: Optional raw content to process
            
        Returns:
            Union[NarratorModel, NarratorError]: Processed section or error
        """
        try:
            # Check cache first
            existing_content = await self.narrator_manager.get_section_content(section_number)
            if not isinstance(existing_content, NarratorError):
                self.logger.info(f"Content found in cache for section {section_number}")
                return existing_content

            # Get content if not provided
            if raw_content is None:
                raw_content = await self.narrator_manager.get_raw_section_content(section_number)
                if not raw_content:
                    return NarratorError(
                        section_number=section_number,
                        message=f"Section {section_number} not found"
                    )

            # Format content with LLM
            narrator_model = await self._format_content(section_number, raw_content)
            
            # Save to cache if processing successful
            if not narrator_model.error:
                save_result = await self.narrator_manager.save_section_content(narrator_model)
                if isinstance(save_result, NarratorError):
                    self.logger.error(f"Failed to save content: {save_result.message}")
            
            return narrator_model

        except Exception as e:
            self.logger.error(f"Error processing section {section_number}: {str(e)}")
            return NarratorModel(
                section_number=section_number,
                content=raw_content,
                error=f"Error processing section: {str(e)}",
                source_type=SourceType.ERROR,
                timestamp=datetime.now()
            )

    async def _format_content(self, section_number: int, content: str) -> NarratorModel:
        """Format content using LLM.
        
        Args:
            section_number: Section number
            content: Raw content to format
            
        Returns:
            NarratorModel: Formatted content model
        """
        try:
            messages = [
                SystemMessage(content=self.config.system_message),
                HumanMessage(content=f"Format this content for section {section_number}:\n\n{content}")
            ]
            
            response = await self.config.llm.ainvoke(messages)
            formatted_content = response.content
            
            return NarratorModel(
                section_number=section_number,
                content=formatted_content,
                source_type=SourceType.RAW,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error formatting content: {str(e)}")
            return NarratorModel(
                section_number=section_number,
                content=content,
                error=f"Error formatting content: {str(e)}",
                source_type=SourceType.ERROR,
                timestamp=datetime.now()
            )

    async def ainvoke(self, input_data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Process game state and update narrative.
        
        Args:
            input_data: Input data containing game state
            
        Yields:
            Dict[str, Any]: Updated game state with narrative
        """
        try:
            game_state = GameState.model_validate(input_data)
            
            # Process current section
            section_result = await self.process_section(game_state.section_number)
            
            if isinstance(section_result, NarratorError):
                self.logger.error(f"Error processing section: {section_result.message}")
                error_model = NarratorModel(
                    section_number=game_state.section_number,
                    content="",
                    error=section_result.message,
                    source_type=SourceType.ERROR,
                    timestamp=datetime.now()
                )
                yield {"narrative": error_model.model_dump()}
                return
                
            # Update game state with processed content
            game_state.narrative_content = section_result.content
            game_state.last_update = datetime.now()
            
            yield {"narrative": section_result.model_dump()}
            
        except Exception as e:
            self.logger.error(f"Error in ainvoke: {str(e)}")
            error_model = NarratorModel(
                section_number=input_data.get("section_number", 1),
                content="",
                error=f"Error in agent invocation: {str(e)}",
                source_type=SourceType.ERROR,
                timestamp=datetime.now()
            )
            yield {"narrative": error_model.model_dump()}
