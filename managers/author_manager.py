"""
Author Manager Module
Handles author-specific functionality like sections management and knowledge graph.
"""

from typing import Dict, Any, List
from pathlib import Path
from loguru import logger

class AuthorManager:
    """Manages author-specific functionality."""

    def __init__(self):
        """Initialize AuthorManager."""
        logger.info("Initializing AuthorManager")
        self.sections_dir = Path("data/sections")
        logger.debug("AuthorManager initialized with sections dir: {}", self.sections_dir)

    async def get_sections(self) -> List[Dict[str, Any]]:
        """Get available game sections.
        
        Returns:
            List[Dict[str, Any]]: List of available sections with metadata
        """
        logger.info("Getting game sections from {}", self.sections_dir)
        sections = []
        
        if not self.sections_dir.exists():
            logger.warning("Sections directory not found: {}", self.sections_dir)
            return []
            
        for section_file in self.sections_dir.glob("*.md"):
            try:
                section_number = int(section_file.stem)
                content = section_file.read_text(encoding='utf-8')
                
                # Parse metadata from content
                lines = content.split('\n')
                title = lines[0].strip('# ') if lines else f"Section {section_number}"
                description = lines[1] if len(lines) > 1 else ""
                
                sections.append({
                    "number": section_number,
                    "title": title,
                    "description": description,
                    "path": str(section_file)
                })
                
            except ValueError:
                logger.warning("Invalid section file name: {}", section_file.name)
            except Exception as e:
                logger.error("Error processing section {}: {}", section_file.name, str(e))
        
        return sorted(sections, key=lambda x: x["number"])

    async def get_knowledge_graph(self) -> Dict[str, Any]:
        """Get game knowledge graph.
        
        Returns:
            Dict[str, Any]: Knowledge graph data with nodes and links
            
        The graph is built from section files, analyzing:
        - Section numbers and titles for nodes
        - Links between sections using [[number]] format
        - Relationships between sections
        """
        logger.info("Building knowledge graph from sections")
        try:
            sections = await self.get_sections()
            
            # Créer les nœuds
            nodes = [
                {
                    "id": str(section["number"]),
                    "title": section["title"],
                    "description": section["description"],
                    "type": "section"
                }
                for section in sections
            ]
            
            # Créer un dictionnaire des nœuds pour validation
            node_ids = {str(section["number"]) for section in sections}
            
            # Créer les liens
            links = []
            for section in sections:
                content = Path(section["path"]).read_text(encoding='utf-8')
                
                # Trouver tous les liens [[X]] dans le contenu
                import re
                section_links = re.findall(r'\[\[(\d+)\]\]', content)
                
                # Ajouter les liens valides
                for target in section_links:
                    # Vérifier que la section cible existe
                    if target in node_ids:
                        links.append({
                            "source": str(section["number"]),
                            "target": target,
                            "type": "section_link"
                        })
            
            logger.info(
                "Knowledge graph built with {} nodes and {} links",
                len(nodes),
                len(links)
            )
            
            return {
                "nodes": nodes,
                "links": links
            }
            
        except Exception as e:
            logger.error("Error building knowledge graph: {}", str(e))
            return {"nodes": [], "links": []}
