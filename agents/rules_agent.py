"""RulesAgent Module
Handles game rules analysis and validation using LLM.
"""

from typing import Dict, Optional, Any, List, AsyncGenerator
from datetime import datetime
import json
from pydantic import BaseModel, Field
from langchain.schema.messages import SystemMessage, HumanMessage
from models.game_state import GameState
from models.rules_model import RulesModel, DiceType, SourceType
from models.errors_model import RulesError
from agents.base_agent import BaseAgent
from agents.protocols.base_agent_protocol import BaseAgentProtocol
from config.agents.rules_agent_config import RulesAgentConfig
from config.logging_config import get_logger
from managers.protocols.rules_manager_protocol import RulesManagerProtocol
from agents.protocols import RulesAgentProtocol

logger = get_logger('rules_agent')

class RulesAgent(BaseAgent, RulesAgentProtocol):
    """Agent responsible for rules analysis."""
    
    config: RulesAgentConfig = Field(default_factory=RulesAgentConfig)

    def __init__(self, config: RulesAgentConfig, rules_manager: RulesManagerProtocol):
        """Initialize the agent with configuration.
        
        Args:
            config: Agent configuration
            rules_manager: Rules manager instance
        """
        super().__init__(config=config)
        self.rules_manager = rules_manager
        self.logger = logger

    async def process_section_rules(self, section_number: int, content: Optional[str] = None) -> RulesModel:
        """Process and analyze rules for a game section.
        
        Args:
            section_number: Section number
            content: Optional section content
            
        Returns:
            RulesModel: Analyzed rules with dice requirements, conditions and choices
        """
        try:
            # Check cache first
            existing_rules = await self.rules_manager.get_existing_rules(section_number)
            if not isinstance(existing_rules, RulesError):
                self.logger.info(f"Rules found in cache for section {section_number}")
                return existing_rules

            # Get content if not provided
            if content is None:
                content = self.rules_manager.get_rules_content(section_number)
                if not content:
                    raise ValueError(f"No content found for section {section_number}")
                
            # Extract rules with LLM
            rules = await self._extract_rules_with_llm(section_number, content)
            
            # Save to cache if analysis successful
            if not rules.error:
                save_result = await self.rules_manager.save_rules(rules)
                if isinstance(save_result, RulesError):
                    self.logger.error(f"Failed to save rules: {save_result.message}")
                
            return rules
            
        except Exception as e:
            self.logger.error(f"Error analyzing rules for section {section_number}: {e}")
            return RulesModel(
                section_number=section_number,
                error=f"Error analyzing rules: {str(e)}",
                source="error",
                source_type=SourceType.ERROR,
                last_update=datetime.now()
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
                
                rules_data = json.loads(response.content)
                rules_data["section_number"] = section_number
                rules_data["source"] = "llm_analysis"
                rules_data["source_type"] = SourceType.PROCESSED
                rules_data["last_update"] = datetime.now()
                
                return RulesModel(**rules_data)
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing LLM response: {e}")
                return RulesModel(
                    section_number=section_number,
                    error=f"Error parsing LLM response: {str(e)}",
                    source="error",
                    source_type=SourceType.ERROR,
                    last_update=datetime.now()
                )
                
        except Exception as e:
            self.logger.error(f"Error in LLM analysis: {e}")
            return RulesModel(
                section_number=section_number,
                error=f"Error in LLM analysis: {str(e)}",
                source="error",
                source_type=SourceType.ERROR,
                last_update=datetime.now()
            )

    async def ainvoke(self, input_data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Method for async interface."""
        try:
            game_state = GameState(**input_data)
            section_number = game_state.section_number
            content = input_data.get("content")
            
            rules = await self.process_section_rules(section_number, content)
            
            yield {"rules": rules.model_dump()}
            
        except Exception as e:
            self.logger.error(f"Error in RulesAgent.ainvoke: {e}")
            error_rules = RulesModel(
                section_number=input_data.get("section_number", 1),
                error=f"Error in agent invocation: {str(e)}",
                source="error",
                source_type=SourceType.ERROR,
                last_update=datetime.now()
            )
            yield {"rules": error_rules.model_dump()}
