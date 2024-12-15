from langchain.schema.runnable import RunnableSerializable
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Optional, List, AsyncGenerator
import logging
from event_bus import EventBus, Event
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.chat_models.base import BaseChatModel
import os

class RulesAgent(BaseModel):
    """
    Agent qui analyse les règles du jeu.
    """
    llm: BaseChatModel = Field(default_factory=lambda: ChatOpenAI(
        model="gpt-4o-mini",
        model_kwargs={
            "system_message": """Tu es un expert en règles de livre-jeu.
            Tu dois analyser les règles et déterminer les actions possibles."""
        }
    ))
    event_bus: EventBus = Field(default_factory=EventBus)
    rules_directory: str = Field(default="data/rules")
    cache: Dict[int, Dict] = Field(default_factory=dict)
    logger: logging.Logger = Field(default_factory=lambda: logging.getLogger(__name__))

    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def invoke(self, input_data: Dict, config: Optional[Dict] = None) -> Dict:
        """
        Analyse les règles d'une section.
        
        Args:
            input_data (Dict): Les données d'entrée avec l'état du jeu
            config (Optional[Dict]): Configuration optionnelle
            
        Returns:
            Dict: Les règles analysées et les actions possibles
        """
        try:
            state = input_data.get("state", {})
            section_number = state.get("section_number")
            
            if not section_number:
                return {
                    "state": {
                        "error": "Section number required",
                        "choices": [],
                        "needs_dice": False,
                        "dice_type": None
                    }
                }
                
            # Vérifier si les règles sont déjà dans l'état
            if "rules" in state:
                rules = state["rules"]
            # Vérifier si le contenu est fourni directement
            elif "content" in state:
                content = state["content"]
                rules_lower = content.lower()
                needs_dice = "dice" in rules_lower or "roll" in rules_lower or "dés" in rules_lower
                dice_type = None
                
                if needs_dice:
                    if any(word in rules_lower for word in ["combat", "fight", "battle", "monstre"]):
                        dice_type = "combat"
                    elif any(word in rules_lower for word in ["chance", "luck", "fortune"]):
                        dice_type = "chance"
                
                rules = {
                    "content": content,
                    "needs_dice": needs_dice,
                    "dice_type": dice_type,
                    "choices": ["Continue"]
                }
            # Sinon vérifier le cache
            elif section_number in self.cache:
                rules = dict(self.cache[section_number])  # Copie profonde
            # Sinon analyser les règles
            else:
                rules = await self._analyze_rules(section_number)
                self.cache[section_number] = dict(rules)  # Copie profonde
            
            # Émettre l'événement (toujours, même si depuis le cache)
            event_data = {
                "section_number": section_number,
                "rules": rules
            }
            if self.event_bus:
                await self.event_bus.emit(
                    Event(type="rules_generated", data=event_data)
                )
            
            # Mettre à jour l'état
            return {
                "state": {
                    **state,
                    "rules": rules,
                    "needs_dice": rules.get("needs_dice", False),
                    "dice_type": rules.get("dice_type"),
                    "choices": rules.get("choices", ["Continue"]),
                    "awaiting_action": rules.get("needs_dice", False)
                },
                "source": "cache" if section_number in self.cache else "loaded"
            }
            
        except Exception as e:
            self.logger.error(f"Error in RulesAgent: {str(e)}")
            raise

    async def _analyze_rules(self, section_number: int) -> Dict:
        """
        Analyse les règles d'une section spécifique.
        
        Args:
            section_number (int): Numéro de la section
            
        Returns:
            Dict: Les règles analysées avec leur structure
        """
        try:
            messages = [
                SystemMessage(content="""Tu es un agent qui analyse les règles d'une section.
Retourne les choix possibles et si un jet de dés est nécessaire."""),
                HumanMessage(content=f"Section: {section_number}")
            ]
            
            response = await self.llm.ainvoke(messages)
            content = response.content
            
            # Analyser si des dés sont nécessaires
            rules_lower = content.lower()
            needs_dice = "dice" in rules_lower or "roll" in rules_lower or "dés" in rules_lower
            dice_type = None
            
            if needs_dice:
                if any(word in rules_lower for word in ["combat", "fight", "battle"]):
                    dice_type = "combat"
                elif any(word in rules_lower for word in ["chance", "luck", "fortune"]):
                    dice_type = "chance"
            
            # Structurer les règles
            rules = {
                "content": content,
                "needs_dice": needs_dice,
                "dice_type": dice_type,
                "choices": ["Continue"]  # Par défaut
            }
            
            return rules
            
        except Exception as e:
            self.logger.error(f"Error analyzing rules: {str(e)}")
            raise

    async def stream(
        self, input_data: Dict, config: Optional[Dict] = None
    ) -> AsyncGenerator[Dict, None]:
        """
        Stream les résultats de l'analyse des règles.
        
        Args:
            input_data (Dict): Les données d'entrée
            config (Optional[Dict]): Configuration optionnelle
            
        Yields:
            Dict: Les résultats de l'analyse
        """
        try:
            result = await self.invoke(input_data, config)
            yield result
            
        except Exception as e:
            self.logger.error(f"Error in stream: {str(e)}")
            raise

    # Alias pour la compatibilité avec les tests
    ainvoke = stream
