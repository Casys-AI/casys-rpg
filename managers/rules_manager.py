"""
Rules Manager Module
Handles game rules analysis and caching.
"""

from typing import Dict, Optional, Any, Union
from datetime import datetime
import logging
from pathlib import Path

from config.storage_config import StorageConfig
from managers.protocols.cache_manager_protocol import CacheManagerProtocol
from managers.protocols.rules_manager_protocol import RulesManagerProtocol
from models.rules_model import RulesModel, DiceType, SourceType
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
- Next Sections: {', '.join(map(str, rules.next_sections)) if rules.next_sections else 'None'}
- Choices: {', '.join(rules.choices) if rules.choices else 'None'}

## Summary
{rules.rules_summary}

## Error
{rules.error or 'None'}
"""

    def _markdown_to_rules(self, content: str, section_number: int) -> Optional[RulesModel]:
        """Parse markdown content to RulesModel."""
        try:
            # Simple markdown parser
            lines = content.split('\n')
            metadata = {}
            analysis = {}
            summary = []
            error = None
            
            current_section = None
            for line in lines:
                if line.startswith('# Rules for Section'):
                    continue
                elif line.startswith('## Metadata'):
                    current_section = 'metadata'
                elif line.startswith('## Analysis'):
                    current_section = 'analysis'
                elif line.startswith('## Summary'):
                    current_section = 'summary'
                elif line.startswith('## Error'):
                    current_section = 'error'
                elif line.strip() and current_section:
                    if current_section == 'metadata':
                        if line.startswith('- '):
                            key, value = line[2:].split(': ', 1)
                            metadata[key.lower()] = value
                    elif current_section == 'analysis':
                        if line.startswith('- '):
                            key, value = line[2:].split(': ', 1)
                            analysis[key.lower()] = value
                    elif current_section == 'summary':
                        summary.append(line)
                    elif current_section == 'error':
                        error = line.strip() if line.strip() != 'None' else None

            return RulesModel(
                section_number=section_number,
                last_update=datetime.fromisoformat(metadata['last update']),
                source=metadata['source'],
                source_type=SourceType(metadata['source type']),
                needs_dice=analysis['needs dice'].lower() == 'true',
                dice_type=DiceType(analysis['dice type'].lower()),
                needs_user_response=analysis['needs user response'].lower() == 'true',
                next_action=None if analysis['next action'] == 'None' else analysis['next action'],
                conditions=[] if analysis['conditions'] == 'None' else [c.strip() for c in analysis['conditions'].split(',')],
                next_sections=[] if analysis['next sections'] == 'None' else [int(s.strip()) for s in analysis['next sections'].split(',')],
                choices=[] if analysis['choices'] == 'None' else [c.strip() for c in analysis['choices'].split(',')],
                rules_summary='\n'.join(summary).strip(),
                error=error
            )
        except Exception as e:
            self.logger.error(f"Error parsing markdown for section {section_number}: {str(e)}")
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
            return await self.cache.exists_raw_content(section_number, "sections")
        except Exception as e:
            self.logger.error(f"Error checking rules existence for section {section_number}: {str(e)}")
            return False
