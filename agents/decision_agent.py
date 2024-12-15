from langchain.schema.runnable import RunnableSerializable
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, AsyncGenerator, Optional, List
from typing import Dict, Optional, Any, List
from agents.base_agent import BaseAgent
from event_bus import Event
import logging
from event_bus import EventBus
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.chat_models.base import BaseChatModel
from agents.rules_agent import RulesAgent

class DecisionAgent(BaseModel):
    """
    Agent responsable des décisions.
    """
    
    llm: BaseChatModel = Field(default_factory=lambda: ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        model_kwargs={
            "system_message": """Tu es un agent de décision pour un livre-jeu.
            Tu dois analyser les réponses du joueur et déterminer les actions à effectuer."""
        }
    ))
    event_bus: EventBus = Field(default_factory=EventBus)
    rules_agent: Optional[RulesAgent] = Field(default=None)
    system_prompt: str = Field(default="""Tu es un agent qui analyse les réponses de l'utilisateur.
Détermine la prochaine section en fonction de la réponse.""")
    logger: logging.Logger = Field(default_factory=lambda: logging.getLogger(__name__))
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
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

            # Si on a besoin d'un jet de dés et qu'on n'en a pas
            if rules.get("needs_dice", False) and not state.get("dice_result"):
                updated_state = {
                    **state,
                    "section_number": section_number,
                    "awaiting_action": "dice_roll",
                    "dice_type": rules.get("dice_type", "normal"),
                    "analysis": "En attente du jet de dés"
                }
                return {"state": updated_state}

            # Si on n'a pas de réponse utilisateur
            if not user_response:
                updated_state = {
                    **state,
                    "section_number": section_number,
                    "awaiting_action": "user_response",
                    "choices": rules.get("choices", []),
                    "analysis": "En attente de la réponse de l'utilisateur"
                }
                return {"state": updated_state}
            
            # Si on a une réponse et un résultat de dés si nécessaire
            analysis = await self._analyze_response(
                section_number, 
                user_response if not state.get("dice_result") else f"{user_response} (Dé: {state.get('dice_result')})",
                rules
            )
            
            # Émettre l'événement
            event = Event(
                type="decision_made",
                data={
                    "section_number": section_number,
                    "analysis": analysis,
                    "dice_result": state.get("dice_result")
                }
            )
            await self.event_bus.emit(event)
            
            # Déterminer la prochaine section en fonction des règles
            next_sections = rules.get("next_sections", [section_number + 1])
            next_section = next_sections[0] if next_sections else section_number + 1
            
            updated_state = {
                **state,
                "next_section": next_section,
                "analysis": analysis,
                "awaiting_action": None
            }
            return {"state": updated_state}
            
        except Exception as e:
            self.logger.error(f"Error in DecisionAgent: {str(e)}")
            return {
                "state": {
                    "error": str(e),
                    "awaiting_action": None,
                    "analysis": None
                }
            }

    async def ainvoke(self, input: Dict[str, Any], *args, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """Prend une décision basée sur l'état actuel."""
        try:
            # Récupérer l'état actuel
            state = await self.get_state()
            section_number = state.get("section_number", 1)
            rules = state.get("rules", {})
            
            # Vérifier si on a besoin d'un lancer de dés
            if rules.get("needs_dice", False):
                decision = {
                    "awaiting_action": "dice_roll",
                    "section_number": section_number,
                    "dice_type": rules.get("dice_type", "normal")
                }
            else:
                # Par défaut, on attend une réponse de l'utilisateur
                decision = {
                    "awaiting_action": "user_input",
                    "section_number": section_number
                }
            
            # Mettre à jour l'état avec la décision
            await self.update_state({
                "decision": decision
            })
            
            # Émettre un événement de décision prise
            await self.emit_event("decision_made", {
                "section": section_number,
                "decision": decision
            })
            
            # Retourner l'état mis à jour
            yield {"state": await self.get_state()}
            
        except Exception as e:
            self.logger.error(f"Erreur dans DecisionAgent: {str(e)}")
            yield {"state": {"error": str(e)}}

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
            
            response = await self.llm.agenerate([messages])
            if not response.generations:
                raise ValueError("No response generated")
            
            analysis = response.generations[0][0].text.strip()
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing response: {str(e)}")
            return f"Error analyzing response: {str(e)}"
