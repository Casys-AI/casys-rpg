"""
Author Manager Protocol
Defines the interface for author-specific functionality.
"""

from typing import Dict, Any, List, Protocol

class AuthorManagerProtocol(Protocol):
    """Protocol for author-specific functionality."""

    async def get_sections(self) -> List[Dict[str, Any]]:
        """Get available game sections.
        
        Returns:
            List[Dict[str, Any]]: List of available sections with metadata
        """
        ...

    async def get_knowledge_graph(self) -> Dict[str, Any]:
        """Get game knowledge graph.
        
        Returns:
            Dict[str, Any]: Knowledge graph data
        """
        ...
