"""RulesAgent Module
Handles game rules analysis and validation using LLM.
"""

from typing import Dict, Optional, Any, List, AsyncGenerator
from datetime import datetime
import json
from pydantic import Field
from langchain_core.messages import SystemMessage, HumanMessage

from models.game_state import GameState
from models.rules_model import RulesModel, DiceType, SourceType
from models.errors_model import RulesError
from agents.base_agent import BaseAgent
from config.agents.rules_agent_config import RulesAgentConfig
from config.logging_config import get_logger
from managers.protocols.rules_manager_protocol import RulesManagerProtocol
from agents.protocols.rules_agent_protocol import RulesAgentProtocol

logger = get_logger('rules_agent')

class RulesAgent(BaseAgent):
    """Agent for analyzing and validating game rules."""
    
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
            self.logger.debug(f"Starting process_section_rules for section {section_number}")
            
            # Check cache first
            cached_rules = await self.rules_manager.get_cached_rules(section_number)
            if cached_rules:
                self.logger.info(f"Rules found in cache for section {section_number}")
                return cached_rules
            
            # Get raw content if not provided
            if not content:
                self.logger.debug("No content provided, fetching raw content")
                raw_content = await self.rules_manager.get_raw_content(section_number)
                if isinstance(raw_content, RulesError):
                    self.logger.error(f"No rules found for section {section_number}")
                    return RulesModel(
                        section_number=section_number,
                        source=SourceType.ERROR,
                        error=raw_content.message
                    )
                content = raw_content
            
            # Extract rules with LLM
            self.logger.info(f"Analyzing rules for section {section_number} with LLM")
            rules = await self._extract_rules_with_llm(section_number, content)
            
            # Save to cache if analysis successful
            if not rules.error:
                self.logger.debug("Analysis successful, saving to cache")
                save_result = await self.rules_manager.save_rules(rules)
                if isinstance(save_result, RulesError):
                    self.logger.error(f"Failed to save rules: {save_result.message}")
                else:
                    self.logger.info("Rules saved successfully")
            
            return rules
            
        except Exception as e:
            self.logger.error(f"Error processing rules: {str(e)}")
            return RulesModel(
                section_number=section_number,
                source=SourceType.ERROR,
                error=str(e)
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
            self.logger.debug(f"Starting LLM extraction for section {section_number}")
            
            messages = [
                SystemMessage(content=self.config.system_message),
                HumanMessage(content=f"""Section Number: {section_number} Content: {content}""")
            ]
            
            response = await self.config.llm.ainvoke(messages)
            
            try:
                # Valider que la réponse est du JSON valide
                content = response.content.strip()
                if not content.startswith('{'):
                    # Si ce n'est pas du JSON, essayer d'extraire le bloc JSON
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    if json_match:
                        content = json_match.group(0)
                    else:
                        raise ValueError("Response does not contain a JSON object")
                
                rules_data = json.loads(content)
                
                # Valider les champs requis
                required_fields = {'needs_dice', 'dice_type', 'needs_user_response', 
                                 'next_action', 'conditions', 'choices', 'rules_summary'}
                missing_fields = required_fields - set(rules_data.keys())
                if missing_fields:
                    # Si des champs sont manquants, fournir des valeurs par défaut
                    defaults = {
                        'needs_dice': False,
                        'dice_type': 'none',
                        'needs_user_response': True,  # Par défaut, on suppose qu'une réponse est nécessaire
                        'next_action': 'user_first',
                        'conditions': [],
                        'choices': [],
                        'rules_summary': content  # Utiliser le contenu comme résumé par défaut
                    }
                    for field in missing_fields:
                        rules_data[field] = defaults[field]
                        self.logger.warning(f"Using default value for missing field: {field}")
                
                # Ajouter les champs supplémentaires
                rules_data["section_number"] = section_number
                rules_data["source"] = "llm_analysis"
                rules_data["source_type"] = SourceType.PROCESSED
                rules_data["last_update"] = datetime.now()
                rules_data["error"] = None
                
                # Convertir les choix en objets Choice
                if "choices" in rules_data:
                    choices = []
                    for choice in rules_data["choices"]:
                        if isinstance(choice, str):
                            # Si le choix est une simple chaîne, créer un choix direct
                            choice = {
                                "text": choice,
                                "type": "direct",
                                "conditions": [],
                                "dice_type": "none",
                                "dice_results": {},
                                "target_section": None
                            }
                        else:
                            # S'assurer que tous les champs optionnels sont présents
                            choice.setdefault("conditions", [])
                            choice.setdefault("dice_type", "none")
                            choice.setdefault("dice_results", {})
                            choice.setdefault("type", "direct")
                            
                            # Convertir les types en minuscules
                            if "type" in choice:
                                choice["type"] = choice["type"].lower()
                            if "dice_type" in choice:
                                choice["dice_type"] = choice["dice_type"].lower()
                                
                        choices.append(choice)
                    rules_data["choices"] = choices
                    
                    self.logger.debug(f"Processed choices: {choices}")
                
                # Créer le modèle
                model = RulesModel(**rules_data)
                self.logger.debug(f"Created RulesModel: {model}")
                return model
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON in LLM response: {e}")
                self.logger.error(f"Response content: {response.content}")
                # Créer un modèle par défaut en cas d'erreur
                return RulesModel(
                    section_number=section_number,
                    needs_dice=False,
                    dice_type="none",
                    needs_user_response=True,
                    next_action="user_first",
                    conditions=[],
                    choices=[],
                    rules_summary=content,
                    error=f"Error parsing LLM response: {str(e)}",
                    source="error",
                    source_type=SourceType.ERROR,
                    last_update=datetime.now()
                )
                
        except Exception as e:
            self.logger.error(f"Error extracting rules with LLM: {e}")
            self.logger.error(f"Section content: {content}")
            # Créer un modèle par défaut en cas d'erreur
            return RulesModel(
                section_number=section_number,
                needs_dice=False,
                dice_type="none",
                needs_user_response=True,
                next_action="user_first",
                conditions=[],
                choices=[],
                rules_summary=content,
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
            
            self.logger.debug(f"Processing section {section_number} with content: {content}")
            
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

    async def invoke(self, input_data: Dict, config: Optional[Dict] = None) -> Dict[str, GameState]:
        """Synchronous invocation of the agent.
        
        Args:
            input_data: Input data for rule validation
            config: Optional configuration
            
        Returns:
            Dict[str, GameState]: Processing results and updated game state
        """
        raise NotImplementedError("Use ainvoke for rules processing")

# Register RulesAgent as implementing RulesAgentProtocol
RulesAgentProtocol.register(RulesAgent)
