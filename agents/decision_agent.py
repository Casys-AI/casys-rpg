from langchain.schema.runnable import RunnableSerializable
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Optional
import logging
from event_bus import EventBus, Event
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.chat_models.base import BaseChatModel

class DecisionAgent(RunnableSerializable[Dict, Dict]):
    """
    Agent responsable des décisions.
    """
    
    llm: BaseChatModel = Field(default_factory=lambda: ChatOpenAI(model="gpt-4o-mini"))
    logger: logging.Logger = Field(default_factory=lambda: logging.getLogger(__name__))
    system_prompt: str = Field(default="""Tu es un agent qui analyse les réponses de l'utilisateur.
Détermine la prochaine section en fonction de la réponse.""")
    event_bus: EventBus = Field(..., description="Bus d'événements pour la communication")

    class Config:
        arbitrary_types_allowed = True

    async def invoke(self, input: Dict) -> Dict:
        """
        Méthode principale appelée par le graph.
        """
        try:
            section_number = input.get("section_number")
            user_response = input.get("user_response")
            rules = input.get("rules", {})
            
            if not section_number:
                raise ValueError("Section number required")

            # Vérifier si un jet de dés est nécessaire
            needs_dice = rules.get("needs_dice", False)
            
            # Si on attend un jet de dés
            if needs_dice and not input.get("dice_result"):
                return {
                    "section_number": section_number,
                    "awaiting_action": "dice_roll",
                    "dice_type": rules.get("dice_type", "normal"),
                    "analysis": "En attente du jet de dés"
                }
            
            # Si on a une réponse utilisateur ou un résultat de dés
            if user_response or input.get("dice_result"):
                # Analyser la situation
                analysis = await self._analyze_response(
                    section_number, 
                    user_response or f"Résultat du dé: {input.get('dice_result')}"
                )
                
                # Émettre l'événement
                event = Event(
                    type="decision_made",
                    data={
                        "section_number": section_number,
                        "analysis": analysis,
                        "dice_result": input.get("dice_result")
                    }
                )
                await self.event_bus.emit(event)
                
                return {
                    "next_section": section_number + 1,
                    "analysis": analysis,
                    "awaiting_action": None
                }
            
            # Si on n'a ni réponse ni dé
            return {
                "section_number": section_number,
                "awaiting_action": "user_input",
                "analysis": "En attente de la réponse de l'utilisateur"
            }

        except Exception as e:
            self.logger.error(f"Error in DecisionAgent: {str(e)}")
            return {"error": str(e)}

    async def _analyze_response(self, section_number: int, user_response: str) -> str:
        """
        Analyse la réponse de l'utilisateur.
        """
        try:
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"Section: {section_number}\nRéponse: {user_response}")
            ]
            
            response = await self.llm.agenerate([messages])
            if not response.generations:
                raise ValueError("No response generated")
                
            analysis = response.generations[0][0].text.strip()
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing response: {str(e)}")
            return f"Error analyzing response: {str(e)}"
