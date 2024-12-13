from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from typing import Dict
import json

class DecisionAgent:
    """
    Agent responsable de la prise de décision basée sur le contexte préparé 
    par l'agent de règles et la réponse de l'utilisateur.
    """
    
    def __init__(self):
        """Initialise l'agent avec le modèle de langage."""
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
    def show_dice_roll_button(self) -> Dict:
        """
        Indique qu'un lancer de dés est nécessaire.
        
        Returns:
            Dict avec:
                needs_dice_roll: True
                message: Message expliquant pourquoi un lancer est nécessaire
        """
        return {
            "needs_dice_roll": True,
            "message": "Un lancer de dés est nécessaire pour continuer."
        }
        
    def decide_next_section(self, context: Dict, user_response: str, dice_result: int = None) -> Dict:
        """
        Détermine la prochaine section en fonction du contexte et de la réponse.
        
        Args:
            context: Contexte préparé par le RulesAgent
            user_response: Réponse de l'utilisateur
            dice_result: Résultat du lancer de dés si déjà effectué
            
        Returns:
            Dict contenant:
                - next_section: numéro de la prochaine section
                - needs_dice_roll: bool, indique si le bouton doit être affiché
                - message: message explicatif si un lancer est nécessaire
                - dice_result: résultat du lancer si fourni
                - explanation: explication de la décision
        """
        # Si un lancer est nécessaire mais pas encore effectué
        if context.get("needs_dice_roll", False) and dice_result is None:
            return self.show_dice_roll_button()
            
        # Préparation du prompt pour le LLM
        system_message = """Tu es un agent de décision qui détermine la prochaine section 
        en fonction du contexte des règles et de la réponse de l'utilisateur. 
        Temperature: 0 - Tu dois suivre strictement les règles."""
        
        # Inclure le résultat du dé dans le contexte si fourni
        context_str = json.dumps(context)
        if dice_result is not None:
            context_str = f"Contexte: {context_str}\nRésultat du lancer de dés: {dice_result}"
        
        human_message = f"""
        Contexte des règles: {context_str}
        Réponse de l'utilisateur: {user_response}
        
        Détermine la prochaine section en suivant strictement les règles.
        Réponds au format JSON avec:
        - next_section: numéro de la section
        - explanation: explication de ta décision
        """
        
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=human_message)
        ]
        
        response = self.llm.invoke(messages)
        try:
            decision = json.loads(response.content)
            decision["dice_result"] = dice_result
            decision["needs_dice_roll"] = False
            return decision
        except json.JSONDecodeError:
            return {
                "error": "Erreur de format dans la réponse de l'agent",
                "next_section": context.get("current_section", 1),
                "needs_dice_roll": False,
                "dice_result": dice_result
            }
