from typing import Dict, Optional, Any, List, AsyncGenerator, Union
from langchain.schema.runnable import RunnableSerializable
from pydantic import BaseModel, ConfigDict, Field
from event_bus import EventBus, Event
from agents.models import GameState
from langchain_openai import ChatOpenAI
from langchain.chat_models.base import BaseChatModel
from langchain.schema import HumanMessage, SystemMessage
from agents.rules_agent import RulesAgent
import logging
import json

# Type pour les agents de règles (réel ou mock)
RulesAgentType = Union[RulesAgent, Any]

class DecisionConfig(BaseModel):
    """Configuration pour DecisionAgent."""
    llm: Optional[BaseChatModel] = Field(default_factory=lambda: ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        model_kwargs={
            "system_message": """Tu es un agent de décision pour un livre-jeu.
            Tu dois analyser les réponses du joueur et déterminer les actions à effectuer."""
        }
    ))
    rules_agent: Optional[RulesAgentType] = None
    system_prompt: str = Field(default="""Tu es un agent qui analyse les réponses de l'utilisateur.
Détermine la prochaine section en fonction de la réponse.""")
    model_config = ConfigDict(arbitrary_types_allowed=True)

class DecisionAgent:
    """
    Agent responsable des décisions.
    """
    
    def __init__(self, event_bus: EventBus, config: Optional[DecisionConfig] = None, **kwargs):
        """
        Initialise l'agent avec une configuration Pydantic.
        
        Args:
            event_bus: Bus d'événements
            config: Configuration Pydantic (optionnel)
            **kwargs: Arguments supplémentaires pour la configuration
        """
        self.event_bus = event_bus
        self.config = config or DecisionConfig(**kwargs)
        self.llm = self.config.llm
        self.rules_agent = self.config.rules_agent
        self.system_prompt = self.config.system_prompt
        self.cache = {}
        self._logger: logging.Logger
        self._setup_logging()
        self.current_rules = None
        
        # Initialiser les événements de manière asynchrone
        import asyncio
        asyncio.create_task(self._setup_events())

    async def _setup_events(self):
        """Configure les abonnements aux événements"""
        await self.event_bus.subscribe("rules_generated", self._on_rules_analyzed)

    def _setup_logging(self):
        """Configure logging without RLock"""
        self._logger = logging.getLogger(__name__)
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.ERROR)

    async def invoke(self, input_data: Dict) -> Dict:
        """
        Méthode principale appelée par le graph.
        
        Args:
            input_data (Dict): Dictionnaire contenant le state avec section_number, user_response, rules, etc.
            
        Returns:
            Dict: État mis à jour avec la décision
        """
        try:
            state = input_data.get("state", {})
            if isinstance(state, GameState):
                state = state.dict()
            
            # Utiliser les règles du state si présentes
            if "rules" in state:
                self.current_rules = state["rules"]
            
            section_number = state.get("section_number")
            user_response = state.get("user_response")
            rules = state.get("rules", {})

            if not section_number:
                return {
                    "state": {
                        "error": "Section number required",
                        "awaiting_action": None,
                        "analysis": None
                    }
                }

            # Vérifier l'ordre des actions si spécifié
            next_action = rules.get("next_action")
            if next_action == "user_first" and not user_response:
                updated_state = state.copy()
                updated_state.update({
                    "section_number": section_number,
                    "awaiting_action": "user_response",
                    "choices": rules.get("choices", []),
                    "analysis": "En attente de la réponse de l'utilisateur"
                })
                return {"state": updated_state}
            elif next_action == "dice_first" and not state.get("dice_result"):
                updated_state = state.copy()
                updated_state.update({
                    "section_number": section_number,
                    "awaiting_action": "dice_roll",
                    "dice_type": rules.get("dice_type", "normal"),
                    "analysis": "En attente du jet de dés"
                })
                return {"state": updated_state}

            # Si pas d'ordre spécifié, vérifier ce qui manque
            # Vérifier d'abord les dés car c'est plus prioritaire
            if rules.get("needs_dice", False) and not state.get("dice_result"):
                updated_state = state.copy()
                updated_state.update({
                    "section_number": section_number,
                    "awaiting_action": "dice_roll",
                    "dice_type": rules.get("dice_type", "normal"),
                    "analysis": "En attente du jet de dés"
                })
                return {"state": updated_state}

            # Ensuite vérifier la réponse utilisateur
            needs_user_response = rules.get("needs_user_response", True)
            if needs_user_response and not user_response:
                updated_state = state.copy()
                updated_state.update({
                    "section_number": section_number,
                    "awaiting_action": "user_response",
                    "choices": rules.get("choices", []),
                    "analysis": "En attente de la réponse de l'utilisateur"
                })
                return {"state": updated_state}

            # Si on a tout ce dont on a besoin, analyser la décision
            return await self._analyze_decision(state)
        except Exception as e:
            self._logger.error(f"Error in DecisionAgent.invoke: {str(e)}")
            return {"state": {"error": str(e)}}

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
            
            # Si on a une réponse utilisateur
            if "user_response" in state:
                choice_idx = int(state["user_response"]) - 1
                if not self.current_rules:
                    self._logger.warning("No rules available for decision")
                    yield {"state": {"error": "No rules available"}}
                    return
                    
                if choice_idx < 0 or choice_idx >= len(self.current_rules["choices"]):
                    self._logger.warning(f"Invalid choice index: {choice_idx}")
                    yield {"state": {"error": "Invalid choice"}}
                    return
                    
                # Mettre à jour l'état avec la section suivante
                next_section = self.current_rules["next_sections"][choice_idx]
                state["section_number"] = next_section
                
                # Émettre l'événement de changement de section
                event = Event(
                    type="section_changed",
                    data={"new_section": next_section}
                )
                await self.event_bus.emit(event)
            
            yield {"state": state}
            
        except Exception as e:
            self._logger.error(f"Error in DecisionAgent.ainvoke: {str(e)}")
            yield {"state": {"error": str(e)}}

    async def _on_rules_analyzed(self, event: Event):
        """
        Gestionnaire d'événement pour rules_generated.
        Met à jour l'état interne avec les nouvelles règles.
        
        Args:
            event (Event): L'événement contenant les règles analysées
        """
        self._logger.debug(f"Received rules for section {event.data['section_number']}")
        self.current_rules = event.data["rules"]

    async def _analyze_response(self, section_number: int, user_response: str, rules: Dict = None) -> str:
        """
        Analyse la réponse de l'utilisateur en tenant compte des règles.
        
        Args:
            section_number: Numéro de la section actuelle
            user_response: Réponse de l'utilisateur
            rules: Règles à appliquer pour l'analyse
        """
        try:
            # Vérifier que la réponse n'est pas None
            if user_response is None:
                return "Pas de réponse à analyser"
            
            # Construire le contexte avec les règles
            context = f"Section: {section_number}\nRéponse: {user_response}"
            if rules:
                context += "\nRègles:\n"
                if "conditions" in rules:
                    context += "- Conditions: " + ", ".join(rules["conditions"]) + "\n"
                if "choices" in rules:
                    context += "- Choix possibles: " + ", ".join(rules["choices"]) + "\n"
                if "next_sections" in rules:
                    context += "- Sections suivantes possibles: " + ", ".join(map(str, rules["next_sections"])) + "\n"
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=context)
            ]
            
            response = await self.llm.ainvoke(messages)
            return response.content.strip()
            
        except Exception as e:
            self._logger.error(f"Error analyzing response: {str(e)}")
            return f"Error analyzing response: {str(e)}"

    async def _analyze_decision(self, state: Dict) -> Dict:
        """
        Analyse la décision en fonction de l'état.
        
        Args:
            state: État actuel
        
        Returns:
            Dict: Décision
        """
        try:
            section_number = state.get("section_number")
            user_response = state.get("user_response")
            dice_result = state.get("dice_result")

            # Vérifier qu'on a un numéro de section
            if not section_number:
                return {"state": {"error": "Numéro de section manquant"}}

            # Obtenir les règles soit depuis current_rules soit depuis rules_agent
            rules = self.current_rules
            if not rules and self.rules_agent:
                rules_result = await self.rules_agent.invoke({
                    "section_number": section_number
                })
                rules = rules_result.get("rules", {})

            if not rules:
                return {"state": {"error": f"Règles non trouvées pour la section {section_number}"}}

            # Vérifier si on a besoin d'un jet de dés
            needs_dice = rules.get("needs_dice", False)
            next_action = rules.get("next_action")  # Optionnel: force l'ordre ("user_first", "dice_first")

            # Si un ordre est spécifié
            if next_action == "user_first" and not user_response:
                updated_state = state.copy()
                updated_state.update({
                    "section_number": section_number,
                    "awaiting_action": "user_response",
                    "choices": rules.get("choices", []),
                    "analysis": "En attente de la réponse de l'utilisateur"
                })
                return {"state": updated_state}
            elif next_action == "dice_first" and not dice_result:
                updated_state = state.copy()
                updated_state.update({
                    "section_number": section_number,
                    "awaiting_action": "dice_roll",
                    "dice_type": rules.get("dice_type", "normal"),
                    "analysis": "En attente du jet de dés"
                })
                return {"state": updated_state}

            # Sinon vérifier ce qui manque
            # Vérifier d'abord les dés car c'est plus prioritaire
            if needs_dice and not dice_result:
                updated_state = state.copy()
                updated_state.update({
                    "section_number": section_number,
                    "awaiting_action": "dice_roll",
                    "dice_type": rules.get("dice_type", "normal"),
                    "analysis": "En attente du jet de dés"
                })
                return {"state": updated_state}

            # Ensuite vérifier la réponse utilisateur
            needs_user_response = rules.get("needs_user_response", True)
            if needs_user_response and not user_response:
                updated_state = state.copy()
                updated_state.update({
                    "section_number": section_number,
                    "awaiting_action": "user_response",
                    "choices": rules.get("choices", []),
                    "analysis": "En attente de la réponse de l'utilisateur"
                })
                return {"state": updated_state}

            # Si on a tout ce dont on a besoin
            analysis = await self._analyze_response(
                section_number, 
                self._format_response(user_response, dice_result),
                rules
            )
            
            # Émettre l'événement
            event = Event(
                type="decision_made",
                data={
                    "section_number": section_number,
                    "analysis": analysis,
                    "dice_result": dice_result,
                    "user_response": user_response
                }
            )
            await self.event_bus.emit(event)
            
            # Déterminer la prochaine section
            next_sections = rules.get("next_sections", [section_number + 1])
            next_section = next_sections[0] if next_sections else section_number + 1
            
            updated_state = state.copy()
            updated_state.update({
                "next_section": next_section,
                "analysis": analysis,
                "awaiting_action": None
            })
            return {"state": updated_state}

        except Exception as e:
            self._logger.error(f"Error in _analyze_decision: {str(e)}")
            return {"state": state}

    def _format_response(self, user_response: Optional[str], dice_result: Optional[int]) -> str:
        """
        Formate la réponse complète avec le résultat du dé si présent.
        """
        if user_response and dice_result:
            return f"{user_response} (Dé: {dice_result})"
        elif user_response:
            return user_response
        elif dice_result:
            return f"Résultat du dé: {dice_result}"
        return ""
