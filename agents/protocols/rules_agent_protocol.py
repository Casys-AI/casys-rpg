"""
Rules Agent Protocol Module
Defines the interface for the Rules Agent
"""

from typing import Dict, Optional, AsyncGenerator, Protocol
from models.rules_model import RulesModel
from agents.protocols.base_agent_protocol import BaseAgentProtocol

class RulesAgentProtocol(BaseAgentProtocol, Protocol):
    """Protocol defining the interface for the Rules Agent."""
    
    async def process_section_rules(self, section_number: int, content: Optional[str] = None) -> RulesModel:
        """
        Process and analyze rules for a game section.
        
        Args:
            section_number: Section number
            content: Optional section content
            
        Returns:
            RulesModel: Analyzed rules with dice requirements, conditions and choices
        """
        ...