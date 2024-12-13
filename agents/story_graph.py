from typing import Dict, Optional, Tuple
import os
import logging

from agents.rules_agent import RulesAgent
from agents.decision_agent import DecisionAgent
from agents.narrator_agent import NarratorAgent
from agents.trace_agent import TraceAgent

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('game.log')
    ]
)

class StoryGraph:
    """
    Gère le flux du jeu et la coordination entre les agents.
    """
    def __init__(self):
        self.logger = logging.getLogger('StoryGraph')
        self.logger.info("StoryGraph initialisé")
        
        # Initialiser les agents
        self.rules_agent = RulesAgent()
        self.decision_agent = DecisionAgent()
        self.narrator_agent = NarratorAgent()
        self.trace_agent = TraceAgent()
        
        # État initial
        self.current_section = 1
        self.logger.info(f"Section courante: {self.current_section}")
        
        # Préparer le contexte de la première section
        self.current_context = self.rules_agent.prepare_context(self.current_section)
    
    def process_user_response(self, user_response: str) -> Dict:
        """
        Traite la réponse de l'utilisateur et détermine la prochaine section.
        
        Args:
            user_response: Réponse de l'utilisateur
            
        Returns:
            Dict avec le résultat du traitement
        """
        self.logger.info(f"Traitement de la réponse utilisateur: '{user_response}'")
        try:
            if self.current_context.get("error"):
                self.logger.error(f"Erreur dans le contexte: {self.current_context['error']}")
                return {"error": self.current_context["error"]}
            
            # Obtenir la décision
            result = self.decision_agent.decide_next_section(
                self.current_context,
                user_response
            )
            
            # Si l'agent de décision demande un lancer de dés
            if result.get("needs_dice_roll", False):
                return {
                    "needs_dice_roll": True,
                    "current_section": self.current_section,
                    "section_content": self.current_context.get("section_content", ""),
                    "message": result.get("message", "Un lancer de dés est nécessaire.")
                }
            
            # Obtenir la prochaine section depuis le résultat
            next_section = result.get("next_section")
            if not next_section:
                return {
                    "error": "Erreur: impossible de déterminer la prochaine section",
                    "current_section": self.current_section,
                    "section_content": self.current_context.get("section_content", "")
                }
            
            # Tracer la décision avant de changer de section
            self.logger.info(f"Transition de section: {self.current_section} -> {next_section}")
            self.trace_agent.record_decision(
                section_number=self.current_section,
                user_response=user_response,
                next_section=next_section,
                context=self.current_context
            )
            
            # Mettre à jour la section courante et préparer le nouveau contexte
            self.current_section = next_section
            self.current_context = self.rules_agent.prepare_context(self.current_section)
            
            # Obtenir le contenu de la nouvelle section
            section_content = self.narrator_agent.get_section_content(self.current_section)
            
            return {
                "section_content": section_content,
                "current_section": self.current_section,
                "error": None
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors du traitement: {str(e)}")
            return {
                "error": f"Une erreur est survenue: {str(e)}",
                "current_section": self.current_section,
                "section_content": self.current_context.get("section_content", "")
            }
    
    def process_dice_result(self, dice_result: int) -> Dict:
        """
        Traite le résultat d'un lancer de dés.
        
        Args:
            dice_result: Résultat du lancer
            
        Returns:
            Dict avec le résultat du traitement
        """
        self.logger.info(f"Traitement du résultat du lancer de dés: {dice_result}")
        try:
            # Préparer le contexte avec les règles
            context = self.rules_agent.prepare_context(self.current_section)
            
            # Obtenir la décision avec le résultat du dé
            result = self.decision_agent.decide_next_section(
                context=context,
                user_response="",  # Pas de réponse utilisateur nécessaire pour un lancer de dés
                dice_result=dice_result
            )
            
            next_section = result["next_section"]
            self.current_section = next_section
            self.logger.info(f"Transition de section: {self.current_section - 1} -> {self.current_section}")
            
            # Obtenir le contenu de la nouvelle section
            self.logger.debug(f"Récupération du contenu de la section {self.current_section}")
            section_content = self.narrator_agent.get_section_content(self.current_section)
            
            # Préparer le contexte de la nouvelle section en parallèle
            self.current_context = self.rules_agent.prepare_context(self.current_section)
            
            # Tracer la décision
            self.logger.debug("Enregistrement de la décision")
            self.trace_agent.record_decision(
                section_number=self.current_section - 1,
                user_response="",
                next_section=next_section,
                context=self.current_context,
                dice_result=dice_result
            )
            
            return {
                "next_section": next_section,
                "section_content": section_content,
                "dice_result": dice_result
            }
        
        except Exception as e:
            self.logger.exception("Erreur lors du traitement du résultat du lancer de dés")
            return {"error": f"Erreur lors du traitement : {str(e)}"}
    
    def get_current_section(self) -> Dict:
        """
        Retourne le contenu de la section actuelle.
        """
        self.logger.info(f"Récupération de la section courante: {self.current_section}")
        try:
            section_content = self.narrator_agent.get_section_content(self.current_section)
            self.logger.debug(f"Type de section_content: {type(section_content)}")
            self.logger.debug(f"Contenu: {section_content[:100]}...")
            
            if not section_content:
                self.logger.error(f"Section {self.current_section} non trouvée")
                return {"error": f"Section {self.current_section} non trouvée"}
                
            result = {
                "section_content": section_content,
                "current_section": self.current_section,
                "error": None
            }
            self.logger.debug(f"Type de result: {type(result)}")
            return result
        except Exception as e:
            self.logger.error(f"Erreur lors de la lecture de la section courante: {str(e)}")
            return {"error": f"Erreur lors de la lecture : {str(e)}"}
            
    def get_section(self, section_number):
        """
        Retourne le contenu d'une section spécifique.
        
        Args:
            section_number: Numéro de la section à récupérer
            
        Returns:
            Contenu de la section
        """
        return self.narrator_agent.get_section_content(section_number)

    def get_character_stats(self) -> Dict:
        """
        Retourne les statistiques du personnage depuis TraceAgent.
        """
        self.logger.info("Récupération des statistiques du personnage")
        return self.trace_agent.get_character_stats()
