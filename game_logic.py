# game_logic.py
from agents.story_graph import StoryGraph, GameState
from agents.narrator_agent import NarratorAgent
from agents.rules_agent import RulesAgent
from agents.decision_agent import DecisionAgent
from agents.trace_agent import TraceAgent
from event_bus import EventBus  # Import correct du EventBus
import logging
import os
from typing import Dict, Optional, Any

# Désactiver les logs des appels API
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("openai._base_client").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpcore.connection").setLevel(logging.WARNING)
logging.getLogger("httpcore.http11").setLevel(logging.WARNING)

class GameLogic:
    """
    Gère l'état du jeu et coordonne les interactions entre les agents.
    """
    
    def __init__(self):
        """Initialise l'état du jeu et les agents."""
        self.logger = logging.getLogger(__name__)
        
        # Créer une instance de l'event bus
        self.event_bus = EventBus()
        
        # Initialiser les agents avec l'event bus
        self.narrator = NarratorAgent(event_bus=self.event_bus)
        self.rules = RulesAgent(event_bus=self.event_bus)
        self.decision = DecisionAgent(rules_agent=self.rules, event_bus=self.event_bus)
        self.trace = TraceAgent(event_bus=self.event_bus)  # Assurez-vous que TraceAgent accepte event_bus
        
        # Initialiser le graph avec les agents et l'event bus
        self.story_graph = StoryGraph(
            event_bus=self.event_bus,
            narrator_agent=self.narrator,
            rules_agent=self.rules,
            decision_agent=self.decision,
            trace_agent=self.trace
        )
        
        self.current_section = 1
        self.logger.info("GameLogic initialisé")
        self.last_error = None
        
    def truncate_for_log(self, content: str, max_length: int = 100) -> str:
        """Tronque une chaîne pour les logs."""
        if not content or len(str(content)) <= max_length:
            return str(content)
        return str(content)[:max_length] + "..."
        
    def check_section_cache(self, section_number: int) -> bool:
        """
        Vérifie si une section est en cache.
        
        Args:
            section_number: Numéro de la section à vérifier
            
        Returns:
            bool: True si la section est en cache
        """
        cache_file = os.path.join("data/sections/cache", f"{section_number}_cached.md")
        return os.path.exists(cache_file)

    async def get_current_section(self) -> Dict:
        """
        Retourne le contenu de la section actuelle.
        
        Returns:
            Dict contenant:
                - content: contenu de la section
                - rules: règles de la section
                - decision: décision si applicable
        """
        try:
            # Vérifier si c'est la première section
            if self.current_section == 1:
                self.logger.info(f"GameLogic - Chargement section initiale {self.current_section}")
                
                # Vérifier si la section 1 est en cache
                if self.check_section_cache(1):
                    self.logger.info("GameLogic - Section 1 trouvée en cache")
                else:
                    self.logger.info("GameLogic - Section 1 non trouvée en cache, traitement requis")
            else:
                self.logger.info(f"GameLogic - Chargement section {self.current_section} (décidé par l'agent)")
                
            # Invoquer le workflow
            result = await self.story_graph.invoke({
                "section_number": self.current_section
            })
            
            self.logger.info(f"GameLogic - Contenu: {self.truncate_for_log(result)}")
            return result
            
        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"GameLogic - Erreur dans get_current_section: {str(e)}")
            return {"error": str(e)}
        
    async def process_response(self, user_response: str) -> Dict:
        """
        Traite la réponse de l'utilisateur et détermine la prochaine section.
        """
        try:
            self.logger.info(f"GameLogic - Traitement réponse: {self.truncate_for_log(user_response)}")
            
            result = await self.story_graph.invoke({
                "section_number": self.current_section,
                "user_response": user_response
            })
            
            if "error" not in result:
                if "decision" in result and "next_section" in result["decision"]:
                    next_section = result["decision"]["next_section"]
                    
                    # Vérifier si la prochaine section est en cache
                    if next_section != self.current_section:
                        if self.check_section_cache(next_section):
                            self.logger.info(f"GameLogic - Section {next_section} trouvée en cache")
                        else:
                            self.logger.info(f"GameLogic - Section {next_section} non trouvée en cache, traitement requis")
                    
                    self.current_section = next_section
                    self.logger.info(f"GameLogic - Nouvelle section: {next_section}")
                else:
                    self.logger.warning("GameLogic - Pas de décision ou de section suivante dans la réponse")
                
            self.logger.info(f"GameLogic - Réponse traitée: {self.truncate_for_log(str(result))}")
            return result
            
        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"GameLogic - Erreur dans process_response: {str(e)}")
            return {"error": str(e)}
    
    async def process_dice_result(self, dice_result: int) -> Dict:
        """
        Traite le résultat d'un lancer de dés.
        
        Args:
            dice_result: Résultat du lancer
            
        Returns:
            Dict avec le résultat du traitement
        """
        try:
            result = await self.story_graph.invoke({
                "section_number": self.current_section,
                "dice_result": dice_result
            })
            
            self.logger.info(f"GameLogic - Résultat dés traité: {self.truncate_for_log(result)}")
            return result
        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"GameLogic - Erreur dans process_dice_result: {str(e)}")
            return {"error": str(e)}
        
    def get_character_stats(self) -> Dict:
        """
        Retourne les statistiques actuelles du personnage.
        
        Returns:
            Dict avec les stats du personnage depuis le fichier de trace
        """
        try:
            return self.trace.get_character_stats()  # Assurez-vous que TraceAgent a cette méthode
        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"GameLogic - Erreur dans get_character_stats: {str(e)}")
            return {"error": str(e)}
