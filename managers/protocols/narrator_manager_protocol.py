"""Protocol for the narrator manager."""
from typing import Optional, Union, Protocol
from models.narrator_model import NarratorModel
from models.errors_model import NarratorError

class NarratorManagerProtocol(Protocol):
    """Protocol defining the interface for narrator managers."""
    
    async def get_section_content(self, section_number: int) -> Optional[Union[NarratorModel, NarratorError]]:
        """Get processed section content.
        
        Args:
            section_number: Section number to retrieve
            
        Returns:
            Optional[Union[NarratorModel, NarratorError]]: Processed section or error
        """
        ...
        
    async def save_section_content(self, content: NarratorModel) -> Optional[NarratorError]:
        """Save section content to storage.
        
        Args:
            content: Content to save
            
        Returns:
            Optional[NarratorError]: Error if any
        """
        ...
        
    async def get_raw_section_content(self, section_number: int) -> Optional[str]:
        """Get raw section content.
        
        Args:
            section_number: Section to retrieve
            
        Returns:
            Optional[str]: Raw content if found
        """
        ...
