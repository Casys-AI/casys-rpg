"""
NarratorAgent Module
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

    async def _process_section(self, section_number: int, content: Optional[str] = None) -> Union[NarratorModel, NarratorError]:
        """Process and format a game section.
        
        Args:
            section_number: Section number to process
            content: Optional raw content to process. If not provided, will be fetched from manager.
            
        Returns:
            Union[NarratorModel, NarratorError]: Processed section content or error
        """
        try:
            logger.debug("Starting process_section for section {}", section_number)
            
            # Check cache first
            cached_content = await self.narrator_manager.get_cached_content(section_number)
            if cached_content:
                logger.info("Content found in cache for section {}", section_number)
                logger.debug("Cached narrative content: {}", 
                           (cached_content.content[:100] + "...") if len(cached_content.content) > 100 else cached_content.content)
                return cached_content
            
            # Get raw content if not provided
            if not content:
                logger.debug("No raw content provided, fetching from manager")
                raw_content_result = await self.narrator_manager.get_raw_content(section_number)
                if isinstance(raw_content_result, NarratorError):
                    logger.error("Failed to get raw content: {}", raw_content_result.message)
                    return raw_content_result
                content = raw_content_result
                logger.debug("Raw content fetched: {}", 
                           (content[:100] + "...") if len(content) > 100 else content)
            
            # Process content with LLM
            logger.info("Processing content for section {} with LLM", section_number)
            processed_result = await self._process_content(section_number, content)
            if isinstance(processed_result, NarratorError):
                logger.error("Failed to process content: {}", processed_result.message)
                return processed_result
                
            logger.debug("Processed narrative content: {}", 
                       (processed_result.content[:100] + "...") if len(processed_result.content) > 100 else processed_result.content)
            
            # Save to cache
            save_result = await self.narrator_manager.save_content(processed_result)
            if isinstance(save_result, NarratorError):
                logger.error("Failed to save content: {}", save_result.message)
                return save_result
                
            return processed_result
            
        except Exception as e:
            logger.error("Error processing section {}: {}", section_number, str(e))
            return NarratorError(
                section_number=section_number,
                message=str(e)
            )

    async def _process_content(self, section_number: int, content: str) -> Union[NarratorModel, NarratorError]:
        """Process content using LLM.
        
        Args:
            section_number: Section number
            content: Raw content to process
            
        Returns:
            Union[NarratorModel, NarratorError]: Processed content model or error
        """
        try:
            logger.debug("Starting content processing with LLM")
            logger.debug("Preparing messages for LLM with section {} and content length {}", section_number, len(content))
            
            messages = [
                SystemMessage(content=self.config.system_message),
                HumanMessage(content=f"""Section Number: {section_number} Content : {content}""")
            ]
            
            logger.debug("Sending request to LLM")
            response = await self.config.llm.ainvoke(messages)
            logger.debug("Received response from LLM: {}", 
                       (response.content[:100] + "...") if len(response.content) > 100 else response.content)
            
            try:
                # Valider que la réponse est du JSON valide
                content = response.content.strip()
                if not content.startswith('{'):
                    # Si ce n'est pas du JSON, essayer d'extraire le bloc JSON
                    logger.debug("Response is not JSON, attempting to extract JSON block")
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    if json_match:
                        content = json_match.group(0)
                        logger.debug("Extracted JSON block: {}", 
                                   (content[:100] + "...") if len(content) > 100 else content)
                    else:
                        logger.error("No JSON object found in response")
                        raise ValueError("Response does not contain a JSON object")
                
                logger.debug("Parsing JSON response")
                response_data = json.loads(content)
                logger.debug("Parsed JSON data: {}", response_data)
                
                # Valider les champs requis
                required_fields = {'content', 'source_type', 'error'}
                missing_fields = required_fields - set(response_data.keys())
                if missing_fields:
                    logger.warning("Missing required fields in response: {}", missing_fields)
                    # Si des champs sont manquants, fournir des valeurs par défaut
                    defaults = {
                        'content': content,  # Utiliser le contenu brut par défaut
                        'source_type': 'processed',
                        'error': None
                    }
                    for field in missing_fields:
                        response_data[field] = defaults[field]
                        logger.warning("Using default value for {}: {}", field, defaults[field])
                
                # Créer le NarratorModel
                logger.debug("Creating NarratorModel")
                model = NarratorModel(
                    section_number=section_number,
                    content=response_data['content'],
                    source_type=SourceType(response_data['source_type'].lower()),
                    error=response_data['error']
                )
                logger.debug("Successfully created NarratorModel: {}", model)
                return model
                
            except json.JSONDecodeError as e:
                logger.error("Invalid JSON in LLM response: {}", str(e))
                logger.error("Response content: {}", response.content)
                return NarratorError(
                    section_number=section_number,
                    message=f"Invalid JSON in LLM response: {str(e)}"
                )
            except Exception as e:
                logger.error("Error parsing LLM response: {}", str(e))
                logger.error("Full error: {}", str(e), exc_info=True)
                return NarratorError(
                    section_number=section_number,
                    message=f"Error parsing LLM response: {str(e)}"
                )
            
        except Exception as e:
            logger.error("Error formatting content: {}", str(e))
            logger.error("Full error: {}", str(e), exc_info=True)
            return NarratorError(
                section_number=section_number,
                message=f"Error formatting content: {str(e)}"
            )

    async def ainvoke(self, input_data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Process game state and update narrative.
        
        Args:
            input_data: Input data containing game state
            
        Yields:
            Dict[str, Any]: Updated narrative content
        """
        try:
            state = input_data.get("state")
            if not state:
                raise ValueError("No state provided in input data")
                
            logger.debug("Processing narrative for state: session={}, section={}", 
                        state.session_id, state.section_number)
            
            # Process section
            result = await self._process_section(state.section_number)
            if isinstance(result, NarratorError):
                yield {"narrative": result}
                return
            
            yield {"narrative": result}
            
        except Exception as e:
            logger.exception("Error in narrator agent: {}", str(e))
            yield {"narrative": NarratorError(message=str(e))}
            
# Register NarratorAgent as implementing NarratorAgentProtocol
NarratorAgentProtocol.register(NarratorAgent)
