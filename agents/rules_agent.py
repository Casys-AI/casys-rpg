from typing import Dict, Optional, Any, List, AsyncGenerator
from langchain.schema.runnable import RunnableSerializable
from pydantic import BaseModel, ConfigDict, Field
from event_bus import EventBus, Event
from agents.models import GameState
from langchain_openai import ChatOpenAI
from langchain.chat_models.base import BaseChatModel
from langchain.schema import HumanMessage, SystemMessage
import logging
import json
import os
import re
from agents.base_agent import BaseAgent

class RulesConfig(BaseModel):
    """Configuration pour RulesAgent."""
    llm: Optional[BaseChatModel] = Field(default_factory=lambda: ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        model_kwargs={
            "system_message": """Tu es un agent d'analyse de règles pour un livre-jeu.
            Tu dois déterminer les règles applicables et les conditions à vérifier."""
        }
    ))
    rules_directory: str = Field(default="data/rules")
    model_config = ConfigDict(arbitrary_types_allowed=True)

class RulesAgent(BaseAgent):
    """Agent responsable de l'analyse des règles."""

    def __init__(self, event_bus: EventBus, config: Optional[RulesConfig] = None, **kwargs):
        """
        Initialise l'agent avec une configuration Pydantic.
        
        Args:
            event_bus: Bus d'événements
            config: Configuration Pydantic (optionnel)
            **kwargs: Arguments supplémentaires pour la configuration
        """
        super().__init__(event_bus)  # Appel au constructeur parent
        self.config = config or RulesConfig(**kwargs)
        self.llm = self.config.llm
        self.rules_directory = self.config.rules_directory
        self.cache = {}
        # self._setup_logging()

    async def invoke(self, input_data: Dict) -> Dict:
        """
        Analyse les règles d'une section.
        
        Args:
            input_data (Dict): Les données d'entrée avec l'état du jeu
            
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
            elif "content" in state or "formatted_content" in state:
                content = state.get("content") or state.get("formatted_content")
                rules_lower = content.lower()
                
                # Détection des dés
                dice_keywords = [
                    "dés", "dé", "dice", "roll", "lancer", "lancez", "tentez",
                    "jet", "jets", "throw", "rolling"
                ]
                
                combat_keywords = [
                    "combat", "fight", "battle", "monstre", "creature", "enemy",
                    "attaquer", "attaque", "combattre", "affronter", "HABILETÉ",
                    "habileté", "skill"
                ]
                
                needs_dice = any(keyword in rules_lower for keyword in dice_keywords)
                
                dice_type = None
                if needs_dice:
                    # Détection du type de jet
                    if any(keyword in rules_lower for keyword in combat_keywords):
                        dice_type = "combat"
                    elif any(word in rules_lower for word in [
                        "chance", "luck", "fortune", "hasard", "tentez votre chance",
                        "test your luck", "tenter votre chance"
                    ]):
                        dice_type = "chance"
                
                rules = {
                    "needs_dice": needs_dice,
                    "dice_type": dice_type,
                    "conditions": [],
                    "next_sections": [],
                    "rules_summary": "",
                    "choices": ["Continue"] if needs_dice else []
                }
            # Sinon vérifier le cache
            elif section_number in self.cache:
                rules = dict(self.cache[section_number])  # Copie profonde
            # Sinon analyser les règles
            else:
                rules = await self._analyze_rules(section_number)
                self.cache[section_number] = dict(rules)  # Copie profonde
            
            # Émettre l'événement
            event_data = {
                "section_number": section_number,
                "rules": rules
            }
            if self.event_bus:
                await self.event_bus.emit(
                    Event(type="rules_generated", data=event_data)
                )
            
            # Mettre à jour l'état
            new_state = state.copy()
            new_state["rules"] = rules
            
            return {"state": new_state}
            
        except Exception as e:
            # self._logger.error(f"Error in RulesAgent: {str(e)}")
            raise

    async def _analyze_rules(self, section_number: int, content: Optional[str] = None) -> Dict:
        """
        Analyse les règles d'une section spécifique.
        
        Args:
            section_number (int): Numéro de la section
            content (Optional[str]): Contenu des règles si fourni directement
            
        Returns:
            Dict: Les règles analysées avec leur structure
        """
        try:
            # Si le contenu n'est pas fourni, charger le fichier de règles
            if content is None:
                content = await self._load_rules_file(section_number)
                if not content:
                    # self._logger.warning(f"No rules file found for section {section_number}")
                    return {
                        "formatted_content": "",
                        "choices": [],
                        "next_sections": [],
                        "needs_dice": False,
                        "dice_type": None,
                        "conditions": []
                    }
            
            # Analyser avec le LLM
            messages = [
                SystemMessage(content="""Tu es un agent qui analyse les règles d'une section de livre-jeu.
Tu dois retourner une structure JSON avec:
- choices: liste des choix possibles (texte)
- next_sections: liste des numéros de sections correspondants aux choix
- needs_dice: booléen indiquant si un jet de dés est nécessaire
- dice_type: type de jet ("combat", "chance" ou null)
- conditions: liste des conditions à vérifier

Retourne uniquement la structure JSON, sans aucun texte avant ou après.

Exemples:
- Si le texte parle de "Combat" ou "monstre" avec des dés: needs_dice = true, dice_type = "combat"
- Si le texte parle de "Chance" ou "Fortune" avec des dés: needs_dice = true, dice_type = "chance"
- Sinon: needs_dice = false, dice_type = null"""),
                HumanMessage(content=f"""Règles de la section {section_number}:
{content}""")
            ]
            
            response = await self.llm.ainvoke(messages)
            
            try:
                # Parser la réponse JSON
                rules = json.loads(response.content)
                # Ajouter le contenu original
                rules["formatted_content"] = content
                return rules
                
            except json.JSONDecodeError as e:
                # self._logger.error(f"Failed to parse LLM response as JSON: {response.content}")
                # Analyser manuellement si le LLM échoue
                rules_lower = content.lower()
                dice_keywords = [
                    "dés", "dé", "dice", "roll", "lancer", "lancez", "tentez",
                    "jet", "jets", "throw", "rolling"
                ]
                
                combat_keywords = [
                    "combat", "fight", "battle", "monstre", "creature", "enemy",
                    "attaquer", "attaque", "combattre", "affronter", "HABILETÉ",
                    "habileté", "skill"
                ]
                
                needs_dice = any(keyword in rules_lower for keyword in dice_keywords)
                dice_type = None
                
                if needs_dice:
                    if any(keyword in rules_lower for keyword in combat_keywords):
                        dice_type = "combat"
                    elif any(word in rules_lower for word in ["chance", "luck", "fortune"]):
                        dice_type = "chance"
                
                return {
                    "formatted_content": content,
                    "choices": ["Continue"],
                    "next_sections": [],
                    "needs_dice": needs_dice,
                    "dice_type": dice_type,
                    "conditions": []
                }
            
        except Exception as e:
            # self._logger.error(f"Error analyzing rules: {str(e)}")
            raise

    async def _load_rules_file(self, section_number: int) -> Optional[str]:
        """
        Charge le fichier de règles de manière asynchrone.
        
        Args:
            section_number: Numéro de la section
            
        Returns:
            Optional[str]: Contenu du fichier ou None si non trouvé
        """
        try:
            file_path = os.path.join(self.rules_directory, f"section_{section_number}_rule.md")
            if not os.path.exists(file_path):
                # self._logger.warning(f"Rules file not found for section {section_number}")
                return None
                
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            # self._logger.error(f"Error loading rules file for section {section_number}: {str(e)}")
            return None

    async def ainvoke(
        self, input_data: Dict, config: Optional[Dict] = None
    ) -> AsyncGenerator[Dict, None]:
        """
        Version asynchrone de invoke.
        
        Args:
            input_data (Dict): Les données d'entrée avec l'état du jeu
            config (Optional[Dict]): Configuration optionnelle
            
        Returns:
            AsyncGenerator[Dict, None]: Générateur asynchrone de résultats
        """
        try:
            state = input_data.get("state", input_data)
            
            # Vérifier que section_number est présent et valide
            if "section_number" not in state:
                # self._logger.error("No section number provided")
                yield {
                    "state": {
                        "error": "No section number provided",
                        "needs_dice": False,
                        "dice_type": None,
                        "choices": []
                    },
                    "source": "error"
                }
                return
                
            section_number = state.get("section_number")
            if not isinstance(section_number, int) or section_number < 1:
                # self._logger.error(f"Invalid section number: {section_number}")
                yield {
                    "state": {
                        "error": f"Invalid section number: {section_number}",
                        "needs_dice": False,
                        "dice_type": None,
                        "choices": []
                    },
                    "source": "error"
                }
                return
            
            # Utiliser le contenu fourni s'il existe
            content = state.get("formatted_content")
            
            # Vérifier le cache seulement si pas de contenu direct
            if content is None and section_number in self.cache:
                # self._logger.debug(f"Cache hit for section {section_number}")
                rules = dict(self.cache[section_number])
                state["rules"] = rules
                
                # Émettre l'événement même pour le cache
                event = Event(
                    type="rules_generated",
                    data={
                        "section_number": section_number,
                        "rules": rules,
                        "source": "cache"
                    }
                )
                await self.event_bus.emit(event)
                
                yield {
                    "state": state,
                    "source": "cache"
                }
                return
                
            # Analyser les règles
            rules = await self._analyze_rules(section_number, content)
            
            # Mettre en cache seulement si pas de contenu direct
            if content is None:
                self.cache[section_number] = dict(rules)
            
            # Mettre à jour l'état
            state["rules"] = rules
            
            # Émettre l'événement
            event = Event(
                type="rules_generated",
                data={
                    "section_number": section_number,
                    "rules": rules,
                    "source": "analysis"
                }
            )
            await self.event_bus.emit(event)
            
            # Retourner l'état mis à jour avec la source
            yield {
                "state": state,
                "source": "analysis"
            }
            
        except Exception as e:
            # self._logger.error(f"Error in RulesAgent.ainvoke: {str(e)}")
            yield {
                "state": {
                    "error": str(e),
                    "needs_dice": False,
                    "dice_type": None,
                    "choices": []
                },
                "source": "error"
            }
