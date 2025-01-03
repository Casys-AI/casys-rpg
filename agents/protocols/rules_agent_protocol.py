"""
Rules Agent Protocol Module
Defines the interface for the Rules Agent
"""

from typing import Dict, Optional, Protocol, runtime_checkable, Union, AsyncGenerator
from models.rules_model import RulesModel
from models.errors_model import RulesError
from agents.protocols.base_agent_protocol import BaseAgentProtocol

@runtime_checkable
class RulesAgentProtocol(BaseAgentProtocol, Protocol):
    """Protocol defining the interface for the Rules Agent."""
    
    async def _process_section_rules(
        self, 
        section_number: int,
        content: Optional[str] = None
    ) -> Union[RulesModel, RulesError]:
        """Process rules for a game section.
        
        Args:
            section_number: Section number to process
            content: Optional content to process. If not provided, will be fetched from manager.
            
        Returns:
            Union[RulesModel, RulesError]: Processed rules or error
        """
        ...

    async def ainvoke(self, input_data: Dict) -> AsyncGenerator[Dict, None]:
        """Process game state and update rules.
        
        Args:
            input_data: Input data containing game state
            
        Yields:
            Dict: Updated rules content
        """
        ...