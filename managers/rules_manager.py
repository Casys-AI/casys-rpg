"""
Rules Manager Module
Handles game rules storage and caching.
"""

from typing import Dict, Optional, Any, Union, List
from datetime import datetime
import logging
from pathlib import Path
from loguru import logger
import re

from config.storage_config import StorageConfig
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
from managers.protocols.rules_manager_protocol import RulesManagerProtocol
from models.rules_model import RulesModel, DiceType, SourceType, Choice, ChoiceType
from models.errors_model import RulesError

class RulesManager(RulesManagerProtocol):
    """Manages rules content loading and caching."""

    def __init__(self, config: StorageConfig, cache_manager: CacheManagerProtocol):
        """Initialize RulesManager.
        
        Args:
            config: Storage configuration
            cache_manager: Cache manager instance
        """
        logger.info("Initializing RulesManager")
        self.config = config
        self.cache = cache_manager
        self.logger = logging.getLogger(__name__)
        logger.debug("RulesManager initialized with config: {}", config.__class__.__name__)

    async def get_cached_rules(self, section_number: int) -> Optional[RulesModel]:
        """Get rules from cache only."""
        logger.info("Getting cached rules for section {}", section_number)
        
        try:
            content = await self.cache.get_cached_data(
                key=f"section_{section_number}_rules",
                namespace="rules"
            )
            if not content:
                logger.debug("No rules found in cache for section {}", section_number)
                return None
                
            rules = self._markdown_to_rules(content, section_number)
            if rules:
                logger.info("Successfully retrieved rules for section {} from cache", section_number)
                return rules
                
            logger.warning("Failed to parse cached rules for section {}", section_number)
            return None
            
        except KeyError:
            logger.warning("Invalid namespace for section {}", section_number)
            return None
        except Exception as e:
            logger.error("Error retrieving cached rules: {}", str(e))
            return None

    async def get_raw_content(self, section_number: int) -> Union[str, RulesError]:
        """Get raw content from storage."""
        logger.info("Getting raw content for section {}", section_number)
        
        try:
            # Vérifie dans le namespace raw_content
            if not await self.cache.exists_raw_content(
                key=str(section_number),  # Juste le numéro de section car c'est le même raw_content
                namespace="raw_content"
            ):
                logger.warning("No raw content found for section {}", section_number)
                return RulesError(
                    section_number=section_number,
                    message=f"No raw content found for section {section_number}"
                )
                
            content = await self.cache.load_raw_content(
                key=str(section_number),  # Juste le numéro de section car c'est le même raw_content
                namespace="raw_content"
            )
            if content:
                logger.debug("Found raw content for section {}", section_number)
                return content
                
            logger.warning("Failed to load raw content for section {}", section_number)
            return RulesError(
                section_number=section_number,
                message=f"Failed to load raw content for section {section_number}"
            )
            
        except KeyError:
            logger.error("Invalid namespace for section {}", section_number)
            return RulesError(
                section_number=section_number,
                message="Invalid namespace configuration"
            )
        except Exception as e:
            logger.error("Error loading raw content: {}", str(e))
            return RulesError(
                section_number=section_number,
                message=str(e)
            )

    async def save_rules(self, rules: RulesModel) -> Union[RulesModel, RulesError]:
        """Save rules to cache."""
        logger.info("Saving rules for section {}", rules.section_number)
        
        try:
            content = self._rules_to_markdown(rules)
            await self.cache.save_cached_data(
                key=f"section_{rules.section_number}_rules",
                namespace="rules",
                data=content
            )
            logger.debug("Rules saved successfully for section {}", rules.section_number)
            return rules
            
        except KeyError:
            logger.error("Invalid namespace for section {}", rules.section_number)
            return RulesError(
                section_number=rules.section_number,
                message="Invalid namespace configuration"
            )
        except Exception as e:
            logger.error("Error saving rules: {}", str(e))
            return RulesError(
                section_number=rules.section_number,
                message=str(e)
            )


    def _rules_to_markdown(self, rules: RulesModel) -> str:
        """Convert rules to markdown format."""
        logger.debug("Converting rules to markdown for section {}", rules.section_number)
        
        # Extraire les sections cibles des choix
        target_sections = [str(choice.target_section) for choice in rules.choices if choice.target_section is not None]
        
        # Formater les choix
        choices_text = "No choices available" if not rules.choices else self._format_choices(rules.choices)
        
        return f"""# Rules for Section {rules.section_number}

## Metadata
- Last_Update: {rules.last_update.isoformat()}
- Source: {rules.source}
- Source_Type: {rules.source_type.value}

## Analysis
- Needs_Dice: {rules.needs_dice}
- Dice_Type: {rules.dice_type.value}
- Needs_User_Response: {rules.needs_user_response}
- Next_Action: {rules.next_action or 'None'}
- Conditions: {', '.join(rules.conditions) if rules.conditions else 'None'}
- Target_Sections: {', '.join(target_sections) if target_sections else 'None'}

## Choices
{choices_text}

## Summary
{rules.rules_summary or ''}

## Error
{rules.error or 'None'}
"""

    def _format_choices(self, choices) -> str:
        """Format choices for markdown display."""
        logger.debug("Formatting {} choices", len(choices))
        if not choices:
            return "No choices available"
            
        formatted = []
        for choice in choices:
            conditions = f"\n  - Conditions: {', '.join(choice.conditions)}" if choice.conditions else ""
            dice = f"\n  - Dice_Type: {choice.dice_type.value}" if choice.dice_type else ""
            dice_results = f"\n  - Dice_Results: {choice.dice_results}" if choice.dice_results else ""
            target = f"\n  - Target: Section {choice.target_section}" if choice.target_section else ""
            
            formatted.append(
                f"* {choice.text} (Type: {choice.type.value})"
                f"{conditions}{dice}{dice_results}{target}"
            )
            
        return "\n".join(formatted)

    def _parse_choices(self, content: str) -> List[Choice]:
        """Parse choices from markdown content."""
        logger.debug("Parsing choices from content")
        if content.strip() == "No choices available":
            logger.debug("No choices found in content")
            return []
            
        choices = []
        choice_pattern = r"\* (.*?) \(Type: (.*?)\)((?:\n  - .*)*)"
        
        for match in re.finditer(choice_pattern, content):
            text, choice_type, details = match.groups()
            logger.debug("Parsing choice: '{}'", text)
            
            # Parse details
            conditions = []
            dice_type = None
            dice_results = {}
            target_section = None
            
            if details:
                for line in details.split('\n'):
                    line = line.strip()
                    if line.startswith('- Conditions:'):
                        conditions = [c.strip() for c in line[13:].split(',') if c.strip()]
                        logger.debug("Parsed conditions: {}", conditions)
                    elif line.startswith('- Dice_Type:'):
                        dice_type = DiceType(line[12:].strip().lower())
                        logger.debug("Parsed dice type: {}", dice_type.value if dice_type else None)
                    elif line.startswith('- Dice_Results:'):
                        # Parse dict format "{key: value}"
                        results_str = line[15:].strip()
                        if results_str != '{}':
                            results_str = results_str.strip('{}')
                            for pair in results_str.split(','):
                                key, value = pair.split(':')
                                dice_results[key.strip().strip("'")] = int(value.strip())
                        logger.debug("Parsed dice results: {}", dice_results)
                    elif line.startswith('- Target:'):
                        # Extraire uniquement le nombre de la section
                        section_text = line[16:].strip()  # Skip "Section " prefix
                        try:
                            # Nettoyer le texte et extraire le nombre
                            section_num = ''.join(filter(str.isdigit, section_text))
                            target_section = int(section_num) if section_num else None
                            logger.debug("Parsed target section: {}", target_section if target_section else 0)
                        except ValueError as e:
                            logger.error("Invalid section number in choice: {} - {}", section_text, str(e))
                            target_section = None
            
            try:
                choice = Choice(
                    text=text,
                    type=ChoiceType(choice_type.lower()),
                    target_section=target_section,
                    conditions=conditions,
                    dice_type=dice_type or DiceType.NONE,
                    dice_results=dice_results
                )
                choices.append(choice)
                logger.debug("Choice parsed successfully: '{}'", choice.text)
            except Exception as e:
                logger.error("Error creating choice: {}", str(e), exc_info=True)
                continue
            
        logger.info("Successfully parsed {} choices", len(choices))
        return choices

    def _markdown_to_rules(self, content: str, section_number: int) -> Optional[RulesModel]:
        """Parse markdown content to RulesModel."""
        logger.debug("Parsing markdown content for section {}", section_number)
        
        # Split content into sections
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            if line.startswith('## '):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)
                
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        logger.debug("Parsed sections: {}", list(sections.keys()))
        
        # Vérifier les sections requises
        required_sections = {'Metadata', 'Analysis', 'Choices', 'Summary'}
        missing_sections = required_sections - set(sections.keys())
        if missing_sections:
            logger.error("Missing required sections: {}", ', '.join(missing_sections))
            return None
        
        # Parse metadata
        metadata = {}
        try:
            if 'Metadata' in sections:
                for line in sections['Metadata'].split('\n'):
                    if line.startswith('- '):
                        key, value = line[2:].split(': ', 1)
                        # Convertir la clé en snake_case
                        key = key.replace('_', ' ').lower().replace(' ', '_')
                        metadata[key] = value.strip()
            logger.debug("Parsed metadata: {}", metadata)
        except Exception as e:
            logger.error("Error parsing metadata section: {}", str(e), exc_info=True)
            return None
        
        # Parse analysis
        analysis = {}
        try:
            if 'Analysis' in sections:
                analysis_content = sections['Analysis'].strip()
                if not analysis_content:
                    logger.error("Analysis section is empty")
                    return None
                    
                for line in analysis_content.split('\n'):
                    if line.startswith('- '):
                        key, value = line[2:].split(': ', 1)
                        # Convertir la clé en snake_case
                        key = key.replace('_', ' ').lower().replace(' ', '_')
                        analysis[key] = value.strip()
            logger.debug("Parsed analysis: {}", analysis)
        except Exception as e:
            logger.error("Error parsing analysis section: {}", str(e), exc_info=True)
            return None
        
        # Parse choices
        choices = []
        try:
            if 'Choices' in sections:
                choices = self._parse_choices(sections['Choices'])
            logger.debug("Parsed {} choices", len(choices))
        except Exception as e:
            logger.error("Error parsing choices section: {}", str(e), exc_info=True)
            return None
        
        # Parse summary and error
        summary = []
        error = None
        try:
            if 'Summary' in sections:
                summary = sections['Summary'].split('\n')
                
            if 'Error' in sections:
                error = sections['Error'].strip()
                if error == 'None':
                    error = None
        except Exception as e:
            logger.error("Error parsing summary/error sections: {}", str(e), exc_info=True)
            return None

        # Vérifier si toutes les clés requises sont présentes
        required_keys = ['dice_type', 'needs_dice', 'needs_user_response', 'next_action', 'conditions']
        missing_keys = [key for key in required_keys if key not in analysis]
        if missing_keys:
            logger.error("Missing required keys in analysis: {}", ', '.join(missing_keys))
            logger.error("Available keys: {}", list(analysis.keys()))
            return None
        
        # Create RulesModel
        try:
            model_data = {
                "section_number": section_number,
                "dice_type": DiceType((analysis['dice_type'] or 'none').lower()),
                "needs_dice": analysis['needs_dice'].lower() == 'true',
                "needs_user_response": analysis['needs_user_response'].lower() == 'true',
                "next_action": None if analysis['next_action'] == 'None' else analysis['next_action'],
                "conditions": [] if analysis['conditions'] == 'None' else [c.strip() for c in analysis['conditions'].split(',')],
                "choices": choices,
                "rules_summary": '\n'.join(summary).strip(),
                "error": error,
                "source": metadata['source'],
                "source_type": SourceType((metadata.get('source_type') or 'raw').lower()),
                "last_update": datetime.fromisoformat(metadata.get('last_update', datetime.now().isoformat()))
            }
            
            logger.debug("Creating RulesModel with data: {}", {
                "section_number": section_number,
                "dice_type": model_data["dice_type"],
                "needs_dice": model_data["needs_dice"],
                "needs_user_response": model_data["needs_user_response"],
                "next_action": model_data["next_action"],
                "conditions": model_data["conditions"],
                "choices_count": len(model_data["choices"]),
                "source": model_data["source"],
                "source_type": model_data["source_type"]
            })
            model = RulesModel(**model_data)
            logger.info("Successfully created RulesModel for section {}", section_number)
            return model
        except Exception as e:
            logger.error("Error creating RulesModel: {}", str(e), exc_info=True)
            return None
