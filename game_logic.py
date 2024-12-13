from agents.story_graph import StoryGraph
import logging
from typing import Dict, Optional

class GameState:
    """
    Gère l'état du jeu et coordonne les interactions entre les agents.
    """
    
    def __init__(self):
        """Initialise l'état du jeu."""
        self.logger = logging.getLogger('GameState')
        self.logger.setLevel(logging.WARNING)  # Changer le niveau à WARNING au lieu de INFO
        
        self.story_graph = StoryGraph()
        self.current_section = 1
        self.last_error = None
        
    def get_current_section(self) -> Dict:
        """
        Retourne le contenu de la section actuelle.
        
        Returns:
            Dict contenant:
                - section_content: contenu de la section
                - needs_dice_roll: bool indiquant si un lancer est nécessaire
                - dice_result: résultat du dernier lancer si effectué
        """
        try:
            result = self.story_graph.get_current_section()
            self.logger.info(f"GameState - Type de result: {type(result)}")
            self.logger.info(f"GameState - Contenu: {result}")
            # Les logs seront visibles dans l'interface Streamlit via app.py
            return result
        except Exception as e:
            self.last_error = str(e)
            return {"error": str(e)}
        
    def process_response(self, user_response: str) -> Dict:
        """
        Traite la réponse de l'utilisateur.
        
        Args:
            user_response: Réponse de l'utilisateur
            
        Returns:
            Dict avec le résultat du traitement
        """
        try:
            result = self.story_graph.process_user_response(user_response)
            
            if "error" not in result:
                self.current_section = result.get("current_section", self.current_section)
                
            return result
        except Exception as e:
            self.last_error = str(e)
            return {"error": str(e)}
    
    def process_dice_result(self, dice_result: int) -> Dict:
        """
        Traite le résultat d'un lancer de dés.
        
        Args:
            dice_result: Résultat du lancer
            
        Returns:
            Dict avec le résultat du traitement
        """
        try:
            result = self.story_graph.process_dice_result(
                self.current_section,
                dice_result
            )
            
            if "error" not in result:
                self.current_section = result["next_section"]
                
            return result
        except Exception as e:
            self.last_error = str(e)
            return {"error": str(e)}
        
    def get_character_stats(self) -> Dict:
        """
        Retourne les statistiques actuelles du personnage.
        
        Returns:
            Dict avec les stats du personnage depuis le fichier de trace
        """
        try:
            return self.story_graph.trace_agent.get_character_stats()
        except Exception as e:
            self.last_error = str(e)
            return {"error": str(e)}
