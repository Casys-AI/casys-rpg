"""RulesAgent Module
Handles game rules analysis and validation using LLM.
"""

from typing import Dict, Optional, List, AsyncGenerator
import json
from datetime import datetime
from pydantic import ValidationError, Field
from langchain_core.messages import SystemMessage, HumanMessage

from agents.base_agent import BaseAgent
from models.rules_model import RulesModel, DiceType, SourceType
from managers.cache_manager import CacheManager
from config.agent_config import RulesConfig
from config.logging_config import get_logger
from agents.protocols import RulesAgentProtocol, Protocol  # Ajout de l'import du protocole

logger = get_logger('rules_agent')

class RulesAgent(BaseAgent, RulesAgentProtocol):
    """Agent responsable de l'analyse des règles des sections."""
    
    def __init__(self, config: RulesConfig, cache_manager: CacheManager):
        """Initialize RulesAgent.
        
        Args:
            config: Configuration for the agent
            cache_manager: Cache manager instance
        """
        super().__init__(config=config, cache_manager=cache_manager)
        self.logger = logger

    config: RulesConfig = Field(default_factory=RulesConfig)

    async def process_section_rules(self, section_number: int, content: str) -> RulesModel:
        """Process and analyze rules for a game section.
        
        Args:
            section_number: Section number to analyze
            content: Section content
            
        Returns:
            RulesModel: Analyzed rules with dice requirements, conditions and choices
        """
        try:
            # Check cache first
            cached_rules = self.cache_manager.get_rules_from_cache(section_number)
            if cached_rules:
                logger.info(f"[RulesAgent] Règles trouvées en cache pour section {section_number}")
                return cached_rules
                
            # Extract rules with LLM if not in cache
            rules = await self._extract_rules_with_llm(section_number, content)
            
            # Save to cache if analysis successful
            if not rules.error:
                self.cache_manager.save_rules_to_cache(rules)
                
            return rules
            
        except Exception as e:
            logger.error(f"[RulesAgent] Erreur analyse règles section {section_number}: {e}")
            return RulesModel(
                section_number=section_number,
                error=f"Erreur analyse règles: {str(e)}",
                source="error"
            )

    async def _extract_rules_with_llm(self, section_number: int, content: str) -> RulesModel:
        """Extract rules from section content using LLM.
        
        Args:
            section_number: Section number
            content: Section content to analyze
            
        Returns:
            RulesModel: Extracted rules including dice requirements, conditions and choices
        """
        try:
            messages = [
                SystemMessage(content=self.config.system_message),
                HumanMessage(content=f"Analyze section {section_number}:\n\n{content}")
            ]
            
            response = await self.config.llm.ainvoke(messages)
            
            try:
                # Parse response as JSON
                rules_data = json.loads(response.content)
                rules_data["section_number"] = section_number
                rules_data["source"] = "analysis"
                rules_data["source_type"] = SourceType.RAW
                rules_data["last_update"] = datetime.now()
                
                return RulesModel(**rules_data)
                
            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(f"[RulesAgent] Erreur parsing réponse LLM: {e}")
                return RulesModel(
                    section_number=section_number,
                    error=f"Erreur parsing règles: {str(e)}",
                    source="error"
                )
                
        except Exception as e:
            logger.error(f"[RulesAgent] Erreur analyse LLM: {e}")
            return RulesModel(
                section_number=section_number,
                error=f"Erreur analyse LLM: {str(e)}",
                source="error"
            )

    async def ainvoke(self, input_data: Dict) -> AsyncGenerator[Dict, None]:
        """Méthode pour l'interface asynchrone."""
        try:
            section_number = input_data.get("section_number", 1)
            content = input_data.get("content", "")
            
            rules = await self.process_section_rules(section_number, content)
            
            yield rules.model_dump()
            
        except Exception as e:
            logger.error(f"[RulesAgent] Erreur invocation: {e}")
            yield RulesModel(
                section_number=section_number,
                error=f"Erreur invocation: {str(e)}",
                source="error"
            ).model_dump()
