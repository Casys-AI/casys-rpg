"""NarratorAgent Module
Handles content processing and formatting.
"""

from typing import Dict, Optional, AsyncGenerator, Any, Union
from datetime import datetime
import json
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from agents.base_agent import BaseAgent
from models.game_state import GameState
from models.narrator_model import NarratorModel, SourceType
from models.errors_model import NarratorError
from config.agents.narrator_agent_config import NarratorAgentConfig
from config.logging_config import get_logger
from managers.protocols.narrator_manager_protocol import NarratorManagerProtocol
from agents.protocols.narrator_agent_protocol import NarratorAgentProtocol

logger = get_logger('narrator_agent')

class NarratorAgent(BaseAgent):
    """Agent for processing and formatting game content."""

    def __init__(self, config: NarratorAgentConfig, narrator_manager: NarratorManagerProtocol):
        """Initialize NarratorAgent.
        
        Args:
            config: Configuration for the agent
            narrator_manager: Manager for narrator operations
        """
        super().__init__(config=config)
        self.narrator_manager = narrator_manager
        self.logger = logger

    async def process_section(self, section_number: int, raw_content: Optional[str] = None) -> Union[NarratorModel, NarratorError]:
        """Process and format a game section.
        
        Args:
            section_number: Section number to process
            raw_content: Optional raw content to process. If not provided, will be fetched from manager.
            
        Returns:
            Union[NarratorModel, NarratorError]: Processed section content or error
        """
        try:
            # Get content from manager if not provided
            if not raw_content:
                raw_content = await self.narrator_manager.get_section_content(section_number)
                
            # Process content with LLM
            processed_content = await self._process_content(raw_content)
            
            # Create model
            return NarratorModel(
                section_number=section_number,
                content=processed_content,
                source_type=SourceType.PROCESSED,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error processing section {section_number}: {e}")
            return NarratorError(message=str(e))

    async def _process_content(self, content: str) -> str:
        """Process content using LLM.
        
        Args:
            content: Raw content to process
            
        Returns:
            str: Processed content
        """
        try:
            messages = [
                SystemMessage(content=self.config.system_message),
                HumanMessage(content=f"Format this content:\n\n{content}")
            ]
            
            response = await self.config.llm.ainvoke(messages)
            formatted_content = response.content
            
            return formatted_content
            
        except Exception as e:
            self.logger.error(f"Error formatting content: {e}")
            return content

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
            self.logger.error(f"Error in ainvoke: {e}")
            error_model = NarratorModel(
                section_number=input_data.get("section_number", 1),
                content="",
                error=f"Error in agent invocation: {e}",
                source_type=SourceType.ERROR,
                timestamp=datetime.now()
            )
            yield {"narrative": error_model.model_dump()}

# Register NarratorAgent as implementing NarratorAgentProtocol
NarratorAgentProtocol.register(NarratorAgent)
