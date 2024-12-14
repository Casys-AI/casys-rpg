from langchain.schema.runnable import RunnableSerializable
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Optional
import logging
from event_bus import EventBus, Event
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.chat_models.base import BaseChatModel

class RulesAgent(RunnableSerializable[Dict, Dict]):
    """
    Agent qui analyse les règles du jeu.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    rules_directory: str = Field(default="data/rules")
    cache: Dict[int, str] = Field(default_factory=dict)
    logger: logging.Logger = Field(default_factory=lambda: logging.getLogger(__name__))
    llm: BaseChatModel = Field(default_factory=lambda: ChatOpenAI(model="gpt-4o-mini", 
        system_message="""Analyse les règles d'une section du livre-jeu.
Retourne les choix possibles et si un jet de dés est nécessaire."""))
    event_bus: EventBus = Field(..., description="Bus d'événements pour la communication")
    system_prompt: str = Field(default="""Tu es un agent qui analyse les règles d'une section.
Retourne les choix possibles et si un jet de dés est nécessaire.""")

    async def invoke(self, input_data: Dict) -> Dict:
        """
        Analyse les règles d'une section et retourne les informations nécessaires.
        
        Args:
            input_data (Dict): Dictionnaire contenant section_number et optionnellement rules
            
        Returns:
            Dict: Résultat de l'analyse des règles
        """
        try:
            section_number = input_data.get("section_number")
            if not section_number:
                return {
                    "error": "Section number required",
                    "choices": [],
                    "needs_dice": False,
                    "dice_type": None
                }
            
            if section_number < 0:
                return {
                    "error": "Invalid section number",
                    "choices": [],
                    "needs_dice": False,
                    "dice_type": None
                }

            # Si les règles sont fournies directement
            if "rules" in input_data:
                rules = input_data["rules"]
            # Sinon vérifier le cache
            elif section_number in self.cache:
                rules = self.cache[section_number]
            # Sinon analyser les règles
            else:
                rules = await self._analyze_rules(section_number)
                self.cache[section_number] = rules
            
            # Émettre l'événement
            event_data = {
                "section_number": section_number,
                "rules": rules
            }
            event = Event(type="rules_generated", data=event_data)
            await self.event_bus.emit(event)
            
            # Analyser si des dés sont nécessaires
            rules_lower = rules.lower()
            needs_dice = "dice" in rules_lower or "roll" in rules_lower or "dés" in rules_lower
            dice_type = None
            
            if needs_dice:
                if any(word in rules_lower for word in ["combat", "fight", "battle"]):
                    dice_type = "combat"
                elif any(word in rules_lower for word in ["chance", "luck", "fortune"]):
                    dice_type = "chance"
            
            return {
                "choices": ["Continue"],
                "needs_dice": needs_dice,
                "dice_type": dice_type,
                "rules": rules,
                "awaiting_action": needs_dice
            }

        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse des règles : {str(e)}")
            return {
                "error": str(e),
                "choices": [],
                "needs_dice": False,
                "dice_type": None
            }

    async def _analyze_rules(self, section_number: int) -> str:
        """
        Analyse les règles d'une section.
        """
        try:
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"Section: {section_number}")
            ]
            
            response = await self.llm.agenerate([messages])
            if not response.generations:
                raise ValueError("No response generated")
                
            rules = response.generations[0][0].text.strip()
            return rules
            
        except Exception as e:
            self.logger.warning(f"Rules file not found for section {section_number}")
            return f"No rules found for section {section_number}"
