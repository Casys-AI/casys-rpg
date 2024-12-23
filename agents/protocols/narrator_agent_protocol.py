"""
Narrator Agent Protocol Module
Defines the interface for the Narrator Agent
"""

from typing import Dict, Optional, Union, Protocol, runtime_checkable
from models.narrator_model import NarratorModel
from models.errors_model import NarratorError
from agents.protocols.base_agent_protocol import BaseAgentProtocol

@runtime_checkable
class NarratorAgentProtocol(BaseAgentProtocol, Protocol):
    """Protocol defining the interface for the Narrator Agent."""
    
    async def process_section(self, section_number: int, raw_content: Optional[str] = None) -> Union[NarratorModel, NarratorError]:
        """
        Process and format a game section.
        
        Args:
            section_number: Section number to process
            raw_content: Optional raw content to process. If not provided, will be fetched from manager.
            
        Returns:
            Union[NarratorModel, NarratorError]: Processed section content or error
        """
        ...
