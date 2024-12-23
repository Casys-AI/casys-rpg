"""
Rules Manager Module
Handles game rules analysis and caching.
"""

from typing import Dict, Optional, Any, Union, List
from datetime import datetime
import logging
import re
from pathlib import Path

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
        self.config = config
        self.cache = cache_manager
        self.logger = logging.getLogger(__name__)

    def _rules_to_markdown(self, rules: RulesModel) -> str:
        """Convert rules to markdown format."""
        # Extraire les sections cibles des choix
        target_sections = [str(choice.target_section) for choice in rules.choices if choice.target_section is not None]
        
        return f"""# Rules for Section {rules.section_number}

## Metadata
- Last Update: {rules.last_update.isoformat()}
- Source: {rules.source}
- Source Type: {rules.source_type.value}

## Analysis
- Needs Dice: {rules.needs_dice}
- Dice Type: {rules.dice_type.value}
- Needs User Response: {rules.needs_user_response}
- Next Action: {rules.next_action or 'None'}
- Conditions: {', '.join(rules.conditions) if rules.conditions else 'None'}
- Target Sections: {', '.join(target_sections) if target_sections else 'None'}

## Choices
{self._format_choices(rules.choices)}

## Summary
{rules.rules_summary}

## Error
{rules.error or 'None'}
"""

    def _format_choices(self, choices) -> str:
        """Format choices for markdown display."""
        if not choices:
            return "No choices available"
            
        formatted = []
        for choice in choices:
            conditions = f"\n  - Conditions: {', '.join(choice.conditions)}" if choice.conditions else ""
            dice = f"\n  - Dice Type: {choice.dice_type.value}" if choice.dice_type else ""
            dice_results = f"\n  - Dice Results: {choice.dice_results}" if choice.dice_results else ""
            target = f"\n  - Target: Section {choice.target_section}" if choice.target_section else ""
            
            formatted.append(
                f"* {choice.text} (Type: {choice.type.value})"
                f"{conditions}{dice}{dice_results}{target}"
            )
            
        return "\n".join(formatted)

    def _parse_choices(self, content: str) -> List[Choice]:
        """Parse choices from markdown content."""
        choices = []
        choice_pattern = r"\* (.*?) \(Type: (.*?)\)((?:\n  - .*)*)"
        
        for match in re.finditer(choice_pattern, content):
            text, choice_type, details = match.groups()
            
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
                    elif line.startswith('- Dice Type:'):
                        dice_type = DiceType(line[12:].strip())
                    elif line.startswith('- Dice Results:'):
                        # Parse dict format "{key: value}"
                        results_str = line[15:].strip()
                        if results_str != '{}':
                            results_str = results_str.strip('{}')
                            for pair in results_str.split(','):
                                key, value = pair.split(':')
                                dice_results[key.strip().strip("'")] = int(value.strip())
                    elif line.startswith('- Target:'):
                        target_section = int(line[16:].strip())  # Skip "Section " prefix
            
            choice = Choice(
                text=text,
                type=ChoiceType(choice_type),
                target_section=target_section,
                conditions=conditions,
                dice_type=dice_type,
                dice_results=dice_results
            )
            choices.append(choice)
            
        return choices

    def _markdown_to_rules(self, content: str, section_number: int) -> Optional[RulesModel]:
        """Parse markdown content to RulesModel."""
        try:
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
            
            # Parse metadata
            metadata = {}
            if 'Metadata' in sections:
                for line in sections['Metadata'].split('\n'):
                    if line.startswith('- '):
                        key, value = line[2:].split(': ', 1)
                        metadata[key.lower()] = value
            
            # Parse analysis
            analysis = {}
            if 'Analysis' in sections:
                for line in sections['Analysis'].split('\n'):
                    if line.startswith('- '):
                        key, value = line[2:].split(': ', 1)
                        analysis[key.lower()] = value
            
            # Parse choices
            choices = []
            if 'Choices' in sections:
                choices = self._parse_choices(sections['Choices'])
            
            # Parse summary and error
            summary = []
            if 'Summary' in sections:
                summary = sections['Summary'].split('\n')
                
            error = None
            if 'Error' in sections:
                error = sections['Error'].strip()
                if error == 'None':
                    error = None
            
            # Create RulesModel
            return RulesModel(
                section_number=section_number,
                dice_type=DiceType(analysis['dice type']),
                needs_dice=analysis['needs dice'].lower() == 'true',
                needs_user_response=analysis['needs user response'].lower() == 'true',
                next_action=None if analysis['next action'] == 'None' else analysis['next action'],
                conditions=[] if analysis['conditions'] == 'None' else [c.strip() for c in analysis['conditions'].split(',')],
                choices=choices,
                rules_summary='\n'.join(summary).strip(),
                error=error,
                source=metadata['source'],
                source_type=SourceType(metadata['source type']),
                last_update=datetime.fromisoformat(metadata['last update'])
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing markdown content: {str(e)}")
            return None

    async def get_rules_content(self, section_number: int) -> Optional[str]:
        """Get raw rules content for a section."""
        try:
            return await self.cache.get_cached_content(
                key=f"section_{section_number}_rules",
                namespace="rules"
            )
        except Exception as e:
            self.logger.error(f"Error getting rules content for section {section_number}: {str(e)}")
            return None

    async def get_existing_rules(self, section_number: int) -> Union[RulesModel, RulesError]:
        """Get existing rules for a section."""
        try:
            # Try to get from cache first
            content = await self.get_rules_content(section_number)
            if content:
                rules = self._markdown_to_rules(content, section_number)
                if rules:
                    return rules

            # If not in cache, check if raw rules exist
            if not await self.exists_raw_rules(section_number):
                return RulesError(
                    section_number=section_number,
                    message=f"Rules not found for section {section_number}"
                )

            # Load raw content from file
            raw_content = await self.cache.load_raw_content(section_number, "sections")
            if not raw_content:
                return RulesError(
                    section_number=section_number,
                    message=f"Error loading raw rules for section {section_number}"
                )

            # Parse and save rules
            rules = self._markdown_to_rules(raw_content, section_number)
            if not rules:
                return RulesError(
                    section_number=section_number,
                    message=f"Error parsing rules for section {section_number}"
                )

            await self.save_rules(rules)
            return rules

        except Exception as e:
            self.logger.error(f"Error getting rules for section {section_number}: {str(e)}")
            return RulesError(
                section_number=section_number,
                message=str(e)
            )

    async def save_rules(self, rules: RulesModel) -> Union[RulesModel, RulesError]:
        """Save rules to storage."""
        try:
            # Convert to markdown
            content = self._rules_to_markdown(rules)
            
            # Save to cache
            success = await self.cache.save_cached_content(
                key=f"section_{rules.section_number}_rules",
                namespace="rules",
                data=content
            )
            
            if not success:
                return RulesError(
                    section_number=rules.section_number,
                    message="Failed to save rules to cache"
                )
                
            return rules
            
        except Exception as e:
            self.logger.error(f"Error saving rules: {str(e)}")
            return RulesError(
                section_number=rules.section_number,
                message=str(e)
            )

    async def exists_raw_rules(self, section_number: int) -> bool:
        """Check if rules exist for a section."""
        try:
            return await self.cache.exists_raw_content(str(section_number), "sections")
        except Exception as e:
            self.logger.error(f"Error checking rules existence for section {section_number}: {str(e)}")
            return False
